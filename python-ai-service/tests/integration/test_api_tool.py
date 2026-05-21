import pytest


class TestToolAPI:
    @pytest.mark.asyncio
    async def test_list_tools(self, async_client):
        response = await async_client.get("/ai/tools")
        assert response.status_code == 200
        data = response.json()
        assert "tools" in data
        assert len(data["tools"]) >= 2

    @pytest.mark.asyncio
    async def test_get_definitions(self, async_client):
        response = await async_client.get("/ai/tools/definitions")
        assert response.status_code == 200
        data = response.json()
        assert "tools" in data
        for tool in data["tools"]:
            assert tool["type"] == "function"

    @pytest.mark.asyncio
    async def test_execute_calculator(self, async_client):
        response = await async_client.post("/ai/tools/execute", json={
            "tool_name": "calculator",
            "params": {"expression": "2*3+4"}
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "10" in data["result"]
