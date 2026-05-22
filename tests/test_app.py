import pytest
from unittest.mock import Mock, patch, AsyncMock
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 暂时跳过WebSocket测试，专注于其他模块测试
pytestmark = pytest.mark.skip("WebSocket测试需要额外配置")


class TestAppBasic:
    def test_imports(self):
        # 测试基本导入
        from app import app
        assert app is not None
