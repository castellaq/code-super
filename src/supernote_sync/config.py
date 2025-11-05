"""
설정 관리 모듈
YAML 파일을 통해 동기화 설정을 관리합니다.
"""

import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field


@dataclass
class SyncConfig:
    """동기화 설정 데이터 클래스"""
    source_path: str
    destination_path: str
    file_extensions: List[str] = field(default_factory=lambda: ['*'])
    exclude_patterns: List[str] = field(default_factory=list)
    sync_mode: str = 'one-way'  # 'one-way' or 'two-way'
    auto_sync: bool = True
    sync_interval: int = 5  # 초 단위
    max_file_size_mb: Optional[int] = None


class Config:
    """설정 관리 클래스"""

    DEFAULT_CONFIG = {
        'sync': {
            'source_path': '/path/to/supernote/device',
            'destination_path': '/path/to/backup/location',
            'file_extensions': ['.note', '.pdf', '.txt', '.png', '.jpg'],
            'exclude_patterns': ['.*', '__*'],
            'sync_mode': 'one-way',
            'auto_sync': True,
            'sync_interval': 5,
            'max_file_size_mb': 100,
        },
        'logging': {
            'level': 'INFO',
            'log_file': 'logs/supernote_sync.log',
        }
    }

    def __init__(self, config_path: Optional[str] = None):
        """
        설정 초기화

        Args:
            config_path: 설정 파일 경로 (선택사항)
        """
        self.config_path = Path(config_path) if config_path else Path('config.yaml')
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """설정 파일 로드"""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                    return self._merge_with_defaults(config)
            except Exception as e:
                print(f"설정 파일 로드 실패: {e}")
                print("기본 설정을 사용합니다.")
                return self.DEFAULT_CONFIG.copy()
        else:
            print(f"설정 파일이 없습니다: {self.config_path}")
            print("기본 설정을 사용합니다.")
            return self.DEFAULT_CONFIG.copy()

    def _merge_with_defaults(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """사용자 설정과 기본 설정 병합"""
        merged = self.DEFAULT_CONFIG.copy()

        if 'sync' in config:
            merged['sync'].update(config['sync'])
        if 'logging' in config:
            merged['logging'].update(config['logging'])

        return merged

    def save_config(self, config_path: Optional[str] = None):
        """설정을 파일로 저장"""
        path = Path(config_path) if config_path else self.config_path
        path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(path, 'w', encoding='utf-8') as f:
                yaml.dump(self.config, f, default_flow_style=False, allow_unicode=True)
            print(f"설정이 저장되었습니다: {path}")
        except Exception as e:
            print(f"설정 저장 실패: {e}")

    def get_sync_config(self) -> SyncConfig:
        """동기화 설정 객체 반환"""
        sync_data = self.config.get('sync', {})
        return SyncConfig(**sync_data)

    def get(self, key: str, default: Any = None) -> Any:
        """설정 값 가져오기"""
        keys = key.split('.')
        value = self.config

        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default

        return value if value is not None else default

    def set(self, key: str, value: Any):
        """설정 값 설정"""
        keys = key.split('.')
        config = self.config

        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]

        config[keys[-1]] = value

    def create_example_config(self, output_path: str = 'config.yaml.example'):
        """예시 설정 파일 생성"""
        example_config = self.DEFAULT_CONFIG.copy()
        example_config['sync']['source_path'] = '/media/supernote'
        example_config['sync']['destination_path'] = '/home/user/Supernote/Backup'

        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write("# Supernote Auto Sync - 설정 파일\n\n")
                yaml.dump(example_config, f, default_flow_style=False, allow_unicode=True)
            print(f"예시 설정 파일이 생성되었습니다: {output_path}")
        except Exception as e:
            print(f"예시 설정 파일 생성 실패: {e}")
