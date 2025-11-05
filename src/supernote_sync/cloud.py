"""
슈퍼노트 클라우드 연동 모듈
sncloud 라이브러리를 사용하여 슈퍼노트 클라우드와 통신합니다.
"""

import os
import json
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

try:
    from sncloud import SNClient
    SNCLOUD_AVAILABLE = True
except ImportError:
    SNCLOUD_AVAILABLE = False
    SNClient = None


class SupernoteCloud:
    """슈퍼노트 클라우드 클라이언트 래퍼 클래스"""

    def __init__(self, email: Optional[str] = None, password: Optional[str] = None):
        """
        슈퍼노트 클라우드 클라이언트 초기화

        Args:
            email: 슈퍼노트 계정 이메일
            password: 슈퍼노트 계정 비밀번호
        """
        if not SNCLOUD_AVAILABLE:
            raise ImportError(
                "sncloud 라이브러리가 설치되어 있지 않습니다. "
                "'pip install sncloud'를 실행하세요."
            )

        self.client = SNClient()
        self.email = email
        self.password = password
        self.is_authenticated = False
        self.config_dir = Path.home() / '.config' / 'supernote_sync'
        self.token_file = self.config_dir / 'cloud_token.json'

    def login(self, email: Optional[str] = None, password: Optional[str] = None) -> bool:
        """
        슈퍼노트 클라우드에 로그인

        Args:
            email: 이메일 (선택사항, 생성자에서 제공된 경우 생략 가능)
            password: 비밀번호 (선택사항, 생성자에서 제공된 경우 생략 가능)

        Returns:
            로그인 성공 여부
        """
        email = email or self.email
        password = password or self.password

        if not email or not password:
            raise ValueError("이메일과 비밀번호가 필요합니다.")

        try:
            self.client.login(email, password)
            self.email = email
            self.is_authenticated = True
            self._save_credentials(email)
            return True
        except Exception as e:
            raise Exception(f"로그인 실패: {e}")

    def _save_credentials(self, email: str):
        """
        인증 정보 저장 (이메일과 로그인 시간만 저장)
        실제 토큰은 sncloud가 ~/.config/sncloud/config.json에 자동 저장
        """
        self.config_dir.mkdir(parents=True, exist_ok=True)
        credentials = {
            'email': email,
            'last_login': datetime.now().isoformat()
        }
        try:
            with open(self.token_file, 'w', encoding='utf-8') as f:
                json.dump(credentials, f, indent=2)
        except Exception as e:
            # 저장 실패해도 로그인은 성공한 것으로 처리 (sncloud가 토큰 관리)
            print(f"경고: 로그인 정보 저장 실패 - {e}")

    def _load_credentials(self) -> Optional[Dict[str, Any]]:
        """저장된 인증 정보 로드"""
        if self.token_file.exists():
            try:
                with open(self.token_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return None
        return None

    def is_logged_in(self) -> bool:
        """로그인 상태 확인"""
        return self.is_authenticated

    def list_files(self, path: str = "/") -> List[Dict[str, Any]]:
        """
        클라우드 파일 목록 조회

        Args:
            path: 조회할 경로 (기본값: 루트 디렉토리)

        Returns:
            파일 및 폴더 목록
        """
        try:
            files = self.client.ls(path)
            return files if files else []
        except Exception as e:
            # 더 자세한 오류 메시지
            if 'authentication' in str(e).lower() or 'login' in str(e).lower():
                raise Exception("인증이 필요합니다. 'python main.py cloud-login' 명령을 먼저 실행하세요.")
            raise Exception(f"파일 목록 조회 실패: {e}")

    def download_file(
        self,
        cloud_path: str,
        local_path: Optional[str] = None,
        convert_format: Optional[str] = None
    ) -> str:
        """
        클라우드 파일 다운로드

        Args:
            cloud_path: 클라우드 파일 경로
            local_path: 저장할 로컬 경로 (선택사항)
            convert_format: 변환 포맷 ('pdf' 또는 'png', 선택사항)

        Returns:
            다운로드된 파일의 로컬 경로
        """
        try:
            kwargs = {}
            if local_path:
                # 디렉토리 생성
                Path(local_path).parent.mkdir(parents=True, exist_ok=True)
                kwargs['output'] = local_path
            if convert_format:
                kwargs['format'] = convert_format

            result = self.client.get(cloud_path, **kwargs)
            return result
        except Exception as e:
            if 'authentication' in str(e).lower():
                raise Exception("인증이 필요합니다. 'python main.py cloud-login' 명령을 먼저 실행하세요.")
            raise Exception(f"파일 다운로드 실패: {e}")

    def upload_file(self, local_path: str, cloud_parent: str = "/") -> bool:
        """
        로컬 파일을 클라우드에 업로드

        Args:
            local_path: 업로드할 로컬 파일 경로
            cloud_parent: 업로드할 클라우드 부모 디렉토리

        Returns:
            업로드 성공 여부
        """
        if not self.is_authenticated:
            raise Exception("로그인이 필요합니다.")

        if not Path(local_path).exists():
            raise FileNotFoundError(f"파일이 존재하지 않습니다: {local_path}")

        try:
            self.client.put(local_path, parent=cloud_parent)
            return True
        except Exception as e:
            raise Exception(f"파일 업로드 실패: {e}")

    def create_folder(self, folder_name: str, parent: str = "/") -> bool:
        """
        클라우드에 폴더 생성

        Args:
            folder_name: 생성할 폴더 이름
            parent: 부모 디렉토리 경로

        Returns:
            생성 성공 여부
        """
        if not self.is_authenticated:
            raise Exception("로그인이 필요합니다.")

        try:
            self.client.mkdir(folder_name, parent=parent)
            return True
        except Exception as e:
            raise Exception(f"폴더 생성 실패: {e}")

    def sync_from_cloud(
        self,
        cloud_path: str,
        local_path: str,
        recursive: bool = True
    ) -> int:
        """
        클라우드에서 로컬로 동기화

        Args:
            cloud_path: 클라우드 소스 경로
            local_path: 로컬 대상 경로
            recursive: 재귀적으로 하위 디렉토리까지 동기화

        Returns:
            동기화된 파일 수
        """
        if not self.is_authenticated:
            raise Exception("로그인이 필요합니다.")

        sync_count = 0
        local_dir = Path(local_path)
        local_dir.mkdir(parents=True, exist_ok=True)

        try:
            # 파일 목록 가져오기
            items = self.list_files(cloud_path)

            for item in items:
                item_name = item.get('name', item.get('fileName', ''))
                item_type = item.get('type', item.get('fileType', ''))
                item_path = f"{cloud_path}/{item_name}".replace('//', '/')

                if item_type == 'folder' or item_type == 'directory':
                    # 폴더인 경우
                    if recursive:
                        sub_local_path = local_dir / item_name
                        sync_count += self.sync_from_cloud(
                            item_path,
                            str(sub_local_path),
                            recursive=True
                        )
                else:
                    # 파일인 경우
                    local_file = local_dir / item_name
                    self.download_file(item_path, str(local_file))
                    sync_count += 1

            return sync_count

        except Exception as e:
            raise Exception(f"클라우드 동기화 실패: {e}")

    def get_account_info(self) -> Dict[str, Any]:
        """
        저장된 계정 정보 반환

        Returns:
            계정 정보 딕셔너리
        """
        credentials = self._load_credentials()
        return {
            'email': self.email or (credentials.get('email') if credentials else None),
            'is_authenticated': self.is_authenticated,
            'last_login': credentials.get('last_login') if credentials else None
        }
