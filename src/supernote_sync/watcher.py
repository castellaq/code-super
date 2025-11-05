"""
파일 감시 모듈
파일 시스템의 변경사항을 실시간으로 감지합니다.
"""

import time
from pathlib import Path
from typing import Callable, List, Optional
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent


class SyncEventHandler(FileSystemEventHandler):
    """파일 시스템 이벤트 핸들러"""

    def __init__(
        self,
        callback: Callable[[str, str], None],
        file_extensions: List[str],
        exclude_patterns: List[str]
    ):
        """
        이벤트 핸들러 초기화

        Args:
            callback: 파일 변경 시 호출될 콜백 함수
            file_extensions: 감시할 파일 확장자 리스트
            exclude_patterns: 제외할 패턴 리스트
        """
        super().__init__()
        self.callback = callback
        self.file_extensions = file_extensions
        self.exclude_patterns = exclude_patterns

    def _should_process(self, file_path: str) -> bool:
        """파일을 처리해야 하는지 확인"""
        path = Path(file_path)

        # 디렉토리는 무시
        if path.is_dir():
            return False

        # 제외 패턴 확인
        for pattern in self.exclude_patterns:
            if pattern.startswith('*') and str(path).endswith(pattern[1:]):
                return False
            elif pattern.endswith('*') and str(path).startswith(pattern[:-1]):
                return False
            elif pattern in str(path):
                return False

        # 확장자 확인
        if '*' in self.file_extensions:
            return True

        return path.suffix in self.file_extensions

    def on_created(self, event: FileSystemEvent):
        """파일 생성 이벤트"""
        if not event.is_directory and self._should_process(event.src_path):
            self.callback(event.src_path, 'created')

    def on_modified(self, event: FileSystemEvent):
        """파일 수정 이벤트"""
        if not event.is_directory and self._should_process(event.src_path):
            self.callback(event.src_path, 'modified')

    def on_moved(self, event: FileSystemEvent):
        """파일 이동 이벤트"""
        if hasattr(event, 'dest_path'):
            if not event.is_directory and self._should_process(event.dest_path):
                self.callback(event.dest_path, 'moved')


class FileWatcher:
    """파일 감시 클래스"""

    def __init__(
        self,
        watch_path: str,
        callback: Callable[[str, str], None],
        file_extensions: List[str],
        exclude_patterns: List[str]
    ):
        """
        파일 감시자 초기화

        Args:
            watch_path: 감시할 디렉토리 경로
            callback: 파일 변경 시 호출될 콜백 함수
            file_extensions: 감시할 파일 확장자 리스트
            exclude_patterns: 제외할 패턴 리스트
        """
        self.watch_path = Path(watch_path)
        self.callback = callback
        self.file_extensions = file_extensions
        self.exclude_patterns = exclude_patterns

        self.observer = Observer()
        self.event_handler = SyncEventHandler(
            callback=self.callback,
            file_extensions=self.file_extensions,
            exclude_patterns=self.exclude_patterns
        )

    def start(self):
        """파일 감시 시작"""
        if not self.watch_path.exists():
            raise FileNotFoundError(f"감시 경로가 존재하지 않습니다: {self.watch_path}")

        self.observer.schedule(
            self.event_handler,
            str(self.watch_path),
            recursive=True
        )
        self.observer.start()

    def stop(self):
        """파일 감시 중지"""
        self.observer.stop()
        self.observer.join()

    def is_running(self) -> bool:
        """감시자 실행 상태 확인"""
        return self.observer.is_alive()
