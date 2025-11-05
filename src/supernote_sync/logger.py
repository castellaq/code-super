"""
로깅 시스템
파일 동기화 작업 및 오류를 추적하고 기록합니다.
"""

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional
from colorama import Fore, Style, init

# Colorama 초기화
init(autoreset=True)


class Logger:
    """커스텀 로거 클래스"""

    def __init__(self, name: str = "SupernoteSync", log_file: Optional[str] = None, level: int = logging.INFO):
        """
        로거 초기화

        Args:
            name: 로거 이름
            log_file: 로그 파일 경로 (선택사항)
            level: 로깅 레벨
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        self.logger.handlers.clear()

        # 콘솔 핸들러 설정
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_formatter = ColoredFormatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)

        # 파일 핸들러 설정 (지정된 경우)
        if log_file:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)

            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(level)
            file_formatter = logging.Formatter(
                '%(asctime)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(file_formatter)
            self.logger.addHandler(file_handler)

    def debug(self, message: str):
        """디버그 메시지 로깅"""
        self.logger.debug(message)

    def info(self, message: str):
        """정보 메시지 로깅"""
        self.logger.info(message)

    def warning(self, message: str):
        """경고 메시지 로깅"""
        self.logger.warning(message)

    def error(self, message: str):
        """에러 메시지 로깅"""
        self.logger.error(message)

    def critical(self, message: str):
        """치명적 오류 메시지 로깅"""
        self.logger.critical(message)

    def sync_event(self, source: str, destination: str, action: str = "복사"):
        """동기화 이벤트 로깅"""
        self.info(f"{action}: {source} -> {destination}")


class ColoredFormatter(logging.Formatter):
    """컬러 출력을 위한 포매터"""

    COLORS = {
        'DEBUG': Fore.CYAN,
        'INFO': Fore.GREEN,
        'WARNING': Fore.YELLOW,
        'ERROR': Fore.RED,
        'CRITICAL': Fore.RED + Style.BRIGHT,
    }

    def format(self, record):
        """레코드 포맷팅"""
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = f"{self.COLORS[levelname]}{levelname}{Style.RESET_ALL}"
        return super().format(record)
