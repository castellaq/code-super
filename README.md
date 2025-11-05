# Supernote Auto Sync

슈퍼노트(Supernote) 전자 노트 장치의 파일을 자동으로 동기화하는 시스템입니다.

## 주요 기능

- **실시간 파일 감지**: 슈퍼노트 장치의 파일 변경사항을 실시간으로 감지
- **자동 동기화**: 변경된 파일을 자동으로 백업 위치에 복사
- **파일 필터링**: 특정 확장자만 동기화하도록 설정 가능
- **제외 패턴**: 숨김 파일, 임시 파일 등 제외 가능
- **로깅 시스템**: 모든 동기화 작업을 추적하고 기록
- **CLI 인터페이스**: 사용하기 쉬운 명령줄 도구

## 설치

### 1. 저장소 클론

```bash
git clone <repository-url>
cd code-super
```

### 2. 의존성 설치

```bash
pip install -r requirements.txt
```

또는 개별 설치:

```bash
pip install watchdog PyYAML colorama
```

### 3. 설정 파일 생성

```bash
python main.py init
```

또는 수동으로 설정 파일 복사:

```bash
cp config.yaml.example config.yaml
```

### 4. 설정 파일 편집

`config.yaml` 파일을 열고 경로를 수정하세요:

```yaml
sync:
  source_path: /media/supernote          # 슈퍼노트 장치 경로
  destination_path: /home/user/Backup    # 백업 대상 경로
  file_extensions:
    - .note
    - .pdf
    - .txt
  # ... 기타 설정
```

## 사용법

### 자동 동기화 시작

실시간으로 파일 변경을 감지하고 자동으로 동기화합니다:

```bash
python main.py start
```

종료하려면 `Ctrl+C`를 누르세요.

### 전체 파일 동기화 (일회성)

현재 모든 파일을 한 번에 동기화합니다:

```bash
python main.py sync
```

### 현재 설정 확인

```bash
python main.py config
```

### 동기화 통계 확인

```bash
python main.py stats
```

### 상세 로그 출력

```bash
python main.py start --verbose
```

### 사용자 지정 설정 파일 사용

```bash
python main.py start --config /path/to/config.yaml
```

## 설정 옵션

### 동기화 설정 (sync)

- `source_path`: 슈퍼노트 장치의 경로
- `destination_path`: 백업할 대상 경로
- `file_extensions`: 동기화할 파일 확장자 목록 (모든 파일: `['*']`)
- `exclude_patterns`: 제외할 파일 패턴
- `sync_mode`: 동기화 모드 (`one-way` 또는 `two-way`)
- `auto_sync`: 자동 동기화 활성화 여부
- `sync_interval`: 동기화 간격 (초 단위)
- `max_file_size_mb`: 최대 파일 크기 제한 (MB 단위)

### 로깅 설정 (logging)

- `level`: 로그 레벨 (`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`)
- `log_file`: 로그 파일 저장 경로

## 프로젝트 구조

```
code-super/
├── src/
│   └── supernote_sync/
│       ├── __init__.py       # 패키지 초기화
│       ├── sync.py           # 동기화 로직
│       ├── config.py         # 설정 관리
│       ├── watcher.py        # 파일 감시
│       └── logger.py         # 로깅 시스템
├── main.py                   # CLI 진입점
├── config.yaml               # 설정 파일
├── config.yaml.example       # 설정 파일 예시
├── requirements.txt          # Python 의존성
└── README.md                 # 문서
```

## 사용 시나리오

### 시나리오 1: USB로 연결된 슈퍼노트 자동 백업

1. 슈퍼노트를 USB로 연결 (예: `/media/supernote`에 마운트)
2. `config.yaml`에서 경로 설정
3. `python main.py start` 실행
4. 슈퍼노트에서 파일을 생성/수정하면 자동으로 백업됨

### 시나리오 2: 특정 폴더만 동기화

```yaml
sync:
  source_path: /media/supernote/Note
  file_extensions:
    - .note
    - .pdf
```

### 시나리오 3: 정기적인 백업

cron이나 systemd timer를 사용하여 정기적으로 실행:

```bash
# crontab 예시
0 */6 * * * cd /path/to/code-super && python main.py sync
```

## 문제 해결

### 권한 오류

```bash
chmod +x main.py
```

### 경로가 존재하지 않는 경우

설정 파일의 `source_path`가 올바른지 확인하세요. 슈퍼노트가 제대로 마운트되었는지 확인:

```bash
ls -la /media/supernote
```

### 파일이 동기화되지 않는 경우

1. 파일 확장자가 `file_extensions`에 포함되어 있는지 확인
2. `exclude_patterns`에 해당하지 않는지 확인
3. `--verbose` 옵션으로 상세 로그 확인

## 라이선스

MIT License

## 기여

이슈 리포트와 풀 리퀘스트를 환영합니다!

## 참고사항

- 이 프로그램은 슈퍼노트 공식 소프트웨어가 아닙니다
- 중요한 데이터는 항상 추가 백업을 권장합니다
- 양방향 동기화(two-way)는 현재 개발 중입니다
