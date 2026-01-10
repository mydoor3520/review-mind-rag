# Synology Reverse Proxy 설정 가이드

외부에서 `https://mydoor.synology.me/review-mind`로 접근할 수 있도록 Reverse Proxy를 설정합니다.

## 목차

1. [개요](#개요)
2. [Reverse Proxy 설정](#reverse-proxy-설정)
3. [WebSocket 지원](#websocket-지원)
4. [HTTPS 설정](#https-설정)
5. [접근 제어](#접근-제어)
6. [테스트](#테스트)

---

## 개요

### 구성 요약

```
외부 요청
    ↓
https://mydoor.synology.me/review-mind
    ↓
Synology Reverse Proxy (DSM)
    ↓
http://localhost:8510 (Docker 컨테이너)
    ↓
Streamlit 앱
```

### 필요 조건

- Synology DDNS 설정 완료 (`mydoor.synology.me`)
- Let's Encrypt SSL 인증서 (Synology 내장)
- 라우터 포트 포워딩 (443 → NAS)

---

## Reverse Proxy 설정

### 1. 제어판 열기

**제어판 > 로그인 포털 > 고급 > 역방향 프록시**

### 2. 새 규칙 생성

**생성** 버튼 클릭 후 다음 설정 입력:

#### 일반 설정

| 항목 | 값 |
|------|-----|
| 역방향 프록시 이름 | `review-mind-rag` |
| 설명 | RAG 기반 리뷰 분석 시스템 |

#### 소스 (외부 접근)

| 항목 | 값 |
|------|-----|
| 프로토콜 | HTTPS |
| 호스트 이름 | `mydoor.synology.me` |
| 포트 | 443 |
| 경로 | `/review-mind` |

#### 대상 (내부 서비스)

| 항목 | 값 |
|------|-----|
| 프로토콜 | HTTP |
| 호스트 이름 | `localhost` |
| 포트 | `8510` |

### 3. 설정 저장

**확인** 버튼 클릭하여 저장

---

## WebSocket 지원

Streamlit은 WebSocket을 사용하여 실시간 업데이트를 처리합니다. WebSocket 지원을 활성화해야 합니다.

### 커스텀 헤더 설정

역방향 프록시 규칙 편집 > **커스텀 헤더** 탭:

**생성** 버튼 클릭 후 다음 헤더 추가:

| 헤더 이름 | 값 |
|----------|-----|
| `Upgrade` | `$http_upgrade` |
| `Connection` | `$connection_upgrade` |

또는 **WebSocket** 체크박스 활성화 (DSM 7.2+)

---

## HTTPS 설정

### Let's Encrypt 인증서

1. **제어판 > 보안 > 인증서**
2. **추가 > 새 인증서 추가**
3. **Let's Encrypt에서 인증서 얻기** 선택
4. 도메인: `mydoor.synology.me`
5. 이메일 입력 후 **적용**

### 인증서 할당

1. **설정** 버튼 클릭
2. `review-mind-rag` 서비스에 Let's Encrypt 인증서 할당

---

## 접근 제어

### 방법 1: Synology 접근 제어

**제어판 > 보안 > 방화벽**에서 특정 IP만 허용:

```
소스 IP: 허용할 IP 범위 (예: 회사 네트워크)
대상 포트: 443
동작: 허용
```

### 방법 2: 기본 인증 (선택)

Reverse Proxy에서 기본 인증 활성화:

1. 역방향 프록시 규칙 편집
2. **고급 설정** > **HTTP 기본 인증** 활성화
3. 사용자명/비밀번호 설정

---

## 테스트

### 1. 내부 네트워크 테스트

```bash
# NAS 내부에서
curl http://localhost:8510/_stcore/health
# 응답: {"status":"ok"}
```

### 2. 외부 접근 테스트

브라우저에서:
```
https://mydoor.synology.me/review-mind
```

### 3. WebSocket 테스트

Streamlit 앱에서 실시간 업데이트가 작동하는지 확인:
- 질문 입력 시 스피너가 정상적으로 표시되는지
- 결과가 실시간으로 업데이트되는지

### 4. 트러블슈팅

#### 502 Bad Gateway
```bash
# 컨테이너 실행 확인
docker ps | grep review-mind-rag

# 컨테이너 로그 확인
docker logs review-mind-rag
```

#### WebSocket 연결 실패
- 커스텀 헤더 설정 확인
- 브라우저 개발자 도구 > 네트워크 탭에서 WS 연결 확인

#### SSL 인증서 오류
```bash
# 인증서 갱신
/usr/syno/sbin/syno-letsencrypt renew-all
```

---

## 고급 설정

### nginx 직접 설정 (고급 사용자)

SSH로 접속하여 nginx 설정 직접 편집:

```bash
# 설정 파일 위치
/etc/nginx/sites-enabled/

# 설정 확인
nginx -t

# 설정 적용
synoservice --restart nginx
```

### 커스텀 nginx 설정 예시

```nginx
location /review-mind {
    proxy_pass http://localhost:8510;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_read_timeout 86400;
}
```

---

## 참고

- [Synology Reverse Proxy 공식 문서](https://kb.synology.com/en-us/DSM/help/DSM/AdminCenter/application_appportalias)
- [Streamlit 배포 가이드](https://docs.streamlit.io/deploy)
