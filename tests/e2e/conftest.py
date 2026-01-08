"""
E2E 테스트 공통 설정

Playwright를 사용한 Streamlit 앱 E2E 테스트 fixtures
"""

import pytest
import subprocess
import time
import socket
from pathlib import Path
from typing import Generator

# Playwright 플러그인은 루트 conftest.py에서 설정됨


def is_port_open(host: str, port: int, timeout: float = 1.0) -> bool:
    """포트가 열려있는지 확인"""
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except (socket.timeout, ConnectionRefusedError, OSError):
        return False


def wait_for_server(host: str, port: int, timeout: int = 30) -> bool:
    """서버가 준비될 때까지 대기"""
    start_time = time.time()
    while time.time() - start_time < timeout:
        if is_port_open(host, port):
            # Streamlit이 완전히 로드될 때까지 추가 대기
            time.sleep(2)
            return True
        time.sleep(0.5)
    return False


@pytest.fixture(scope="session")
def streamlit_server() -> Generator[str, None, None]:
    """
    Streamlit 서버를 백그라운드에서 실행하고 URL을 반환
    
    테스트 세션 동안 서버를 유지하고, 세션 종료 시 정리
    """
    host = "localhost"
    port = 8502  # 테스트용 포트 (기본 8501과 분리)
    
    # 이미 서버가 실행 중인지 확인
    if is_port_open(host, port):
        yield f"http://{host}:{port}"
        return
    
    # 프로젝트 루트 경로
    project_root = Path(__file__).parent.parent.parent
    app_path = project_root / "app" / "main.py"
    
    # Streamlit 서버 시작
    process = subprocess.Popen(
        [
            "streamlit", "run", str(app_path),
            "--server.port", str(port),
            "--server.headless", "true",
            "--server.address", host,
            "--browser.gatherUsageStats", "false",
        ],
        cwd=str(project_root),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    
    try:
        # 서버 준비 대기
        if not wait_for_server(host, port, timeout=30):
            process.terminate()
            process.wait()
            pytest.fail("Streamlit 서버 시작 실패 (타임아웃)")
        
        yield f"http://{host}:{port}"
    finally:
        # 서버 종료
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args: dict) -> dict:
    """브라우저 컨텍스트 기본 설정"""
    return {
        **browser_context_args,
        "viewport": {"width": 1280, "height": 720},
        "locale": "ko-KR",
        "timezone_id": "Asia/Seoul",
    }


@pytest.fixture
def page_with_server(page, streamlit_server: str):
    """
    Streamlit 서버가 실행된 상태에서 페이지 제공
    
    사용 예:
        def test_main_page(page_with_server):
            page, base_url = page_with_server
            page.goto(base_url)
    """
    page.goto(streamlit_server)
    # Streamlit 앱이 완전히 로드될 때까지 대기
    page.wait_for_load_state("networkidle")
    yield page, streamlit_server


@pytest.fixture
def authenticated_page(page_with_server):
    """
    API 키가 설정된 상태의 페이지 제공
    
    사이드바에서 API 키를 입력한 후 페이지 반환
    """
    page, base_url = page_with_server
    
    # API 키 입력 (테스트용 더미 키 또는 환경 변수에서 가져오기)
    import os
    api_key = os.environ.get("OPENAI_API_KEY", "sk-test-dummy-key")
    
    # 사이드바의 API 키 입력 필드 찾기
    api_input = page.locator("input[type='password']")
    if api_input.is_visible():
        api_input.fill(api_key)
        # 입력 후 약간의 대기 (Streamlit 상태 업데이트)
        page.wait_for_timeout(500)
    
    yield page, base_url
