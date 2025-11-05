"""
동기화 모듈
파일 동기화 로직을 처리합니다.
"""

import shutil
import time
from pathlib import Path
from typing import Optional, List
from datetime import datetime

from .config import Config, SyncConfig
from .logger import Logger
from .watcher import FileWatcher


class SupernoteSync:
    """슈퍼노트 자동 동기화 메인 클래스"""

    def __init__(self, config: Config, logger: Optional[Logger] = None):
        """
        동기화 시스템 초기화

        Args:
            config: 설정 객체
            logger: 로거 객체 (선택사항)
        """
        self.config = config
        self.sync_config = config.get_sync_config()
        self.logger = logger or Logger()

        self.source_path = Path(self.sync_config.source_path)
        self.destination_path = Path(self.sync_config.destination_path)

        self.watcher: Optional[FileWatcher] = None
        self.is_running = False

    def _validate_paths(self) -> bool:
        """경로 유효성 검사"""
        if not self.source_path.exists():
            self.logger.error(f"소스 경로가 존재하지 않습니다: {self.source_path}")
            return False

        # 대상 경로 생성
        self.destination_path.mkdir(parents=True, exist_ok=True)

        return True

    def _should_sync_file(self, file_path: Path) -> bool:
        """파일을 동기화해야 하는지 확인"""
        # 크기 제한 확인
        if self.sync_config.max_file_size_mb:
            max_size_bytes = self.sync_config.max_file_size_mb * 1024 * 1024
            if file_path.stat().st_size > max_size_bytes:
                self.logger.warning(f"파일 크기 제한 초과: {file_path.name}")
                return False

        return True

    def _get_relative_path(self, file_path: Path) -> Path:
        """소스 경로 기준 상대 경로 계산"""
        try:
            return file_path.relative_to(self.source_path)
        except ValueError:
            return file_path

    def sync_file(self, source_file: str, event_type: str = 'modified'):
        """
        개별 파일 동기화

        Args:
            source_file: 소스 파일 경로
            event_type: 이벤트 타입 ('created', 'modified', 'moved')
        """
        source = Path(source_file)

        if not source.exists():
            self.logger.warning(f"파일이 존재하지 않습니다: {source}")
            return

        if not self._should_sync_file(source):
            return

        try:
            # 상대 경로 계산
            relative_path = self._get_relative_path(source)
            destination = self.destination_path / relative_path

            # 대상 디렉토리 생성
            destination.parent.mkdir(parents=True, exist_ok=True)

            # 파일 복사
            shutil.copy2(source, destination)

            self.logger.sync_event(
                str(relative_path),
                str(destination),
                action=f"{event_type} 감지 후 복사"
            )

        except Exception as e:
            self.logger.error(f"파일 동기화 실패: {source} - {e}")

    def sync_all(self):
        """전체 파일 동기화 (초기 동기화)"""
        if not self._validate_paths():
            return

        self.logger.info(f"전체 동기화 시작: {self.source_path} -> {self.destination_path}")

        sync_count = 0
        error_count = 0

        try:
            # 모든 파일 탐색
            for source_file in self.source_path.rglob('*'):
                if source_file.is_file():
                    # 확장자 필터
                    if '*' not in self.sync_config.file_extensions:
                        if source_file.suffix not in self.sync_config.file_extensions:
                            continue

                    # 제외 패턴 확인
                    skip = False
                    for pattern in self.sync_config.exclude_patterns:
                        if pattern in str(source_file):
                            skip = True
                            break

                    if skip:
                        continue

                    try:
                        self.sync_file(str(source_file), 'initial')
                        sync_count += 1
                    except Exception as e:
                        self.logger.error(f"파일 복사 실패: {source_file} - {e}")
                        error_count += 1

            self.logger.info(f"전체 동기화 완료: {sync_count}개 파일 동기화, {error_count}개 오류")

        except Exception as e:
            self.logger.error(f"전체 동기화 중 오류 발생: {e}")

    def _file_change_callback(self, file_path: str, event_type: str):
        """파일 변경 콜백"""
        self.sync_file(file_path, event_type)

    def start_auto_sync(self):
        """자동 동기화 시작"""
        if not self._validate_paths():
            return

        if self.is_running:
            self.logger.warning("자동 동기화가 이미 실행 중입니다.")
            return

        try:
            # 초기 전체 동기화
            self.logger.info("초기 동기화를 수행합니다...")
            self.sync_all()

            # 파일 감시자 시작
            self.watcher = FileWatcher(
                watch_path=str(self.source_path),
                callback=self._file_change_callback,
                file_extensions=self.sync_config.file_extensions,
                exclude_patterns=self.sync_config.exclude_patterns
            )

            self.watcher.start()
            self.is_running = True

            self.logger.info(f"자동 동기화 시작됨: {self.source_path}")
            self.logger.info("변경사항을 실시간으로 감지합니다. 종료하려면 Ctrl+C를 누르세요.")

            # 메인 루프
            while self.is_running:
                time.sleep(1)

        except KeyboardInterrupt:
            self.logger.info("\n사용자에 의해 중단됨")
            self.stop_auto_sync()
        except Exception as e:
            self.logger.error(f"자동 동기화 중 오류 발생: {e}")
            self.stop_auto_sync()

    def stop_auto_sync(self):
        """자동 동기화 중지"""
        if self.watcher and self.watcher.is_running():
            self.watcher.stop()
            self.logger.info("파일 감시자 중지됨")

        self.is_running = False
        self.logger.info("자동 동기화 중지됨")

    def get_sync_stats(self) -> dict:
        """동기화 통계 정보 반환"""
        stats = {
            'source_path': str(self.source_path),
            'destination_path': str(self.destination_path),
            'is_running': self.is_running,
            'sync_mode': self.sync_config.sync_mode,
        }

        if self.source_path.exists():
            source_files = list(self.source_path.rglob('*'))
            stats['source_file_count'] = len([f for f in source_files if f.is_file()])

        if self.destination_path.exists():
            dest_files = list(self.destination_path.rglob('*'))
            stats['destination_file_count'] = len([f for f in dest_files if f.is_file()])

        return stats
