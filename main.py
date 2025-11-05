#!/usr/bin/env python3
"""
Supernote Auto Sync - CLI 인터페이스
슈퍼노트 자동 동기화 시스템의 메인 진입점
"""

import sys
import argparse
import logging
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from supernote_sync import SupernoteSync, Config, Logger, SupernoteCloud


def create_parser() -> argparse.ArgumentParser:
    """명령줄 인자 파서 생성"""
    parser = argparse.ArgumentParser(
        description='Supernote Auto Sync - 슈퍼노트 자동 동기화 시스템',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
  %(prog)s start                    # 자동 동기화 시작
  %(prog)s sync                     # 전체 파일 일회성 동기화
  %(prog)s config                   # 현재 설정 표시
  %(prog)s init                     # 설정 파일 초기화
  %(prog)s stats                    # 동기화 통계 표시

  %(prog)s cloud-login              # 슈퍼노트 클라우드 로그인
  %(prog)s cloud-list               # 클라우드 파일 목록 확인
  %(prog)s cloud-sync               # 클라우드에서 로컬로 동기화

설정 파일:
  기본 위치: config.yaml
  사용자 지정: --config 옵션 사용
        """
    )

    parser.add_argument(
        'command',
        choices=['start', 'sync', 'config', 'init', 'stats', 'cloud-login', 'cloud-list', 'cloud-sync', 'cloud-info'],
        help='실행할 명령'
    )

    parser.add_argument(
        '-c', '--config',
        default='config.yaml',
        help='설정 파일 경로 (기본값: config.yaml)'
    )

    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='상세 로그 출력 (DEBUG 레벨)'
    )

    parser.add_argument(
        '--version',
        action='version',
        version='Supernote Auto Sync v1.1.0'
    )

    parser.add_argument(
        '--cloud-path',
        help='클라우드 경로 (cloud-list, cloud-sync 명령에서 사용)'
    )

    return parser


def cmd_start(config: Config, logger: Logger):
    """자동 동기화 시작"""
    sync = SupernoteSync(config, logger)
    sync.start_auto_sync()


def cmd_sync(config: Config, logger: Logger):
    """전체 파일 일회성 동기화"""
    sync = SupernoteSync(config, logger)
    sync.sync_all()


def cmd_config(config: Config, logger: Logger):
    """현재 설정 표시"""
    print("\n=== 현재 설정 ===\n")

    sync_config = config.get_sync_config()

    print(f"소스 경로:           {sync_config.source_path}")
    print(f"대상 경로:           {sync_config.destination_path}")
    print(f"파일 확장자:         {', '.join(sync_config.file_extensions)}")
    print(f"제외 패턴:           {', '.join(sync_config.exclude_patterns)}")
    print(f"동기화 모드:         {sync_config.sync_mode}")
    print(f"자동 동기화:         {'활성화' if sync_config.auto_sync else '비활성화'}")
    print(f"동기화 간격:         {sync_config.sync_interval}초")

    if sync_config.max_file_size_mb:
        print(f"최대 파일 크기:      {sync_config.max_file_size_mb}MB")
    else:
        print(f"최대 파일 크기:      제한 없음")

    print(f"\n로그 레벨:           {config.get('logging.level')}")
    print(f"로그 파일:           {config.get('logging.log_file')}")
    print()


def cmd_init(config: Config, logger: Logger):
    """설정 파일 초기화"""
    config_path = config.config_path

    if config_path.exists():
        response = input(f"설정 파일이 이미 존재합니다: {config_path}\n덮어쓰시겠습니까? (y/N): ")
        if response.lower() != 'y':
            print("취소되었습니다.")
            return

    # 예시 설정 파일 생성
    config.create_example_config(str(config_path))
    logger.info(f"설정 파일이 생성되었습니다: {config_path}")
    logger.info("설정 파일을 편집하여 경로를 수정하세요.")


def cmd_stats(config: Config, logger: Logger):
    """동기화 통계 표시"""
    sync = SupernoteSync(config, logger)
    stats = sync.get_sync_stats()

    print("\n=== 동기화 통계 ===\n")
    print(f"소스 경로:           {stats['source_path']}")
    print(f"대상 경로:           {stats['destination_path']}")
    print(f"동기화 모드:         {stats['sync_mode']}")
    print(f"실행 상태:           {'실행 중' if stats['is_running'] else '중지됨'}")

    if 'source_file_count' in stats:
        print(f"소스 파일 수:        {stats['source_file_count']}개")

    if 'destination_file_count' in stats:
        print(f"대상 파일 수:        {stats['destination_file_count']}개")

    print()


def cmd_cloud_login(config: Config, logger: Logger):
    """슈퍼노트 클라우드 로그인"""
    import getpass

    try:
        print("\n=== 슈퍼노트 클라우드 로그인 ===\n")

        email = input("이메일: ")
        password = getpass.getpass("비밀번호: ")

        logger.info("로그인 중...")
        cloud = SupernoteCloud()

        if cloud.login(email, password):
            logger.info("로그인 성공!")

            # 설정 파일에 이메일 저장
            config.set('cloud.email', email)
            config.set('cloud.enabled', True)
            config.save_config()

            logger.info(f"계정 정보가 저장되었습니다: {email}")
        else:
            logger.error("로그인 실패")

    except Exception as e:
        logger.error(f"로그인 오류: {e}")


def cmd_cloud_list(config: Config, logger: Logger, args):
    """클라우드 파일 목록 조회"""
    try:
        # 명령줄 인자 우선, 없으면 설정 파일 사용
        cloud_path = args.cloud_path if hasattr(args, 'cloud_path') and args.cloud_path else config.get('cloud.cloud_path', '/')

        logger.info(f"클라우드 경로 '{cloud_path}' 조회 중...")

        # sncloud는 자동으로 ~/.config/sncloud/config.json의 토큰 사용
        cloud = SupernoteCloud()
        cloud.is_authenticated = True  # sncloud가 내부적으로 인증 처리

        files = cloud.list_files(cloud_path)

        print(f"\n=== 클라우드 파일 목록: {cloud_path} ===\n")

        if not files:
            print("파일이 없습니다.")
        else:
            for item in files:
                name = item.get('name', item.get('fileName', '알 수 없음'))
                item_type = item.get('type', item.get('fileType', '파일'))
                size = item.get('size', 0)

                type_icon = "📁" if item_type in ['folder', 'directory'] else "📄"
                size_str = f"{size / 1024:.1f} KB" if size > 0 else ""

                print(f"{type_icon} {name:<40} {size_str}")

        print()

    except Exception as e:
        logger.error(f"파일 목록 조회 실패: {e}")
        if 'verbose' in dir(args) and args.verbose:
            import traceback
            traceback.print_exc()


def cmd_cloud_sync(config: Config, logger: Logger, args):
    """클라우드에서 로컬로 동기화"""
    try:
        cloud_path = args.cloud_path if hasattr(args, 'cloud_path') and args.cloud_path else config.get('cloud.cloud_path', '/')
        local_path = config.get('sync.destination_path')

        logger.info(f"클라우드 동기화 시작: {cloud_path} -> {local_path}")

        # sncloud는 자동으로 토큰 사용
        cloud = SupernoteCloud()
        cloud.is_authenticated = True

        sync_count = cloud.sync_from_cloud(cloud_path, local_path, recursive=True)

        logger.info(f"동기화 완료: {sync_count}개 파일")

    except Exception as e:
        logger.error(f"클라우드 동기화 실패: {e}")
        if hasattr(args, 'verbose') and args.verbose:
            import traceback
            traceback.print_exc()


def cmd_cloud_info(config: Config, logger: Logger):
    """클라우드 계정 정보 표시"""
    try:
        cloud = SupernoteCloud()
        info = cloud.get_account_info()

        print("\n=== 클라우드 계정 정보 ===\n")
        print(f"이메일:              {info.get('email', '없음')}")
        print(f"인증 상태:           {'인증됨' if info.get('is_authenticated') else '미인증'}")

        if info.get('last_login'):
            print(f"마지막 로그인:       {info.get('last_login')}")

        print(f"\n클라우드 활성화:     {'예' if config.get('cloud.enabled') else '아니오'}")
        print(f"클라우드 경로:       {config.get('cloud.cloud_path', '/')}")
        print(f"PDF 변환:            {'예' if config.get('cloud.convert_to_pdf') else '아니오'}")
        print()

    except Exception as e:
        logger.error(f"계정 정보 조회 실패: {e}")


def main():
    """메인 함수"""
    parser = create_parser()
    args = parser.parse_args()

    # 로깅 레벨 설정
    log_level = logging.DEBUG if args.verbose else logging.INFO

    # 설정 로드
    config = Config(args.config)

    # 로거 초기화
    log_file = config.get('logging.log_file')
    logger = Logger(log_file=log_file, level=log_level)

    # 명령 실행
    commands = {
        'start': lambda: cmd_start(config, logger),
        'sync': lambda: cmd_sync(config, logger),
        'config': lambda: cmd_config(config, logger),
        'init': lambda: cmd_init(config, logger),
        'stats': lambda: cmd_stats(config, logger),
        'cloud-login': lambda: cmd_cloud_login(config, logger),
        'cloud-list': lambda: cmd_cloud_list(config, logger, args),
        'cloud-sync': lambda: cmd_cloud_sync(config, logger, args),
        'cloud-info': lambda: cmd_cloud_info(config, logger),
    }

    try:
        commands[args.command]()
    except KeyboardInterrupt:
        logger.info("\n프로그램이 중단되었습니다.")
        sys.exit(0)
    except Exception as e:
        logger.error(f"오류 발생: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
