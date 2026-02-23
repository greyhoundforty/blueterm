"""Tests for InstanceTable widget"""
import pytest
from textual.app import App, ComposeResult

from blueterm.api.models import Instance, InstanceStatus
from blueterm.widgets.instance_table import InstanceTable, ResourceType


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_instance(
    id: str = "inst-001",
    name: str = "my-server",
    status: InstanceStatus = InstanceStatus.RUNNING,
    zone: str = "us-south-1",
    vpc_name: str = "my-vpc",
    vpc_id: str = "vpc-001",
    profile: str = "bx2-2x8",
    primary_ip: str = "10.0.0.1",
) -> Instance:
    return Instance(
        id=id,
        name=name,
        status=status,
        zone=zone,
        vpc_name=vpc_name,
        vpc_id=vpc_id,
        profile=profile,
        primary_ip=primary_ip,
        created_at="2024-01-01T00:00:00Z",
        crn=f"crn:v1:bluemix:public:is:us-south-1::{id}",
    )


class TableApp(App):
    """Minimal app for mounting InstanceTable during tests."""

    def compose(self) -> ComposeResult:
        yield InstanceTable()


# ---------------------------------------------------------------------------
# Unit tests (no app required)
# ---------------------------------------------------------------------------

class TestResourceType:
    def test_enum_values(self):
        assert ResourceType.VPC.value == "vpc"
        assert ResourceType.IKS.value == "iks"
        assert ResourceType.ROKS.value == "roks"
        assert ResourceType.CODE_ENGINE.value == "code_engine"


class TestGetInstanceById:
    def test_found(self):
        table = InstanceTable.__new__(InstanceTable)
        inst = make_instance(id="abc-123")
        table.instances = [inst]
        assert table.get_instance_by_id("abc-123") is inst

    def test_not_found(self):
        table = InstanceTable.__new__(InstanceTable)
        table.instances = [make_instance(id="abc-123")]
        assert table.get_instance_by_id("zzz-999") is None

    def test_empty_list(self):
        table = InstanceTable.__new__(InstanceTable)
        table.instances = []
        assert table.get_instance_by_id("abc-123") is None


class TestProperties:
    def test_instance_count(self):
        table = InstanceTable.__new__(InstanceTable)
        table.instances = [make_instance(), make_instance(id="inst-002")]
        assert table.instance_count == 2

    def test_instance_count_empty(self):
        table = InstanceTable.__new__(InstanceTable)
        table.instances = []
        assert table.instance_count == 0

    def test_has_instances_true(self):
        table = InstanceTable.__new__(InstanceTable)
        table.instances = [make_instance()]
        assert table.has_instances is True

    def test_has_instances_false(self):
        table = InstanceTable.__new__(InstanceTable)
        table.instances = []
        assert table.has_instances is False


class TestSortByColumn:
    def _make_table_with_instances(self, instances):
        """Return a bare InstanceTable with instances set (no widget lifecycle)."""
        table = InstanceTable.__new__(InstanceTable)
        table.instances = instances
        table.resource_type = ResourceType.VPC
        # Stub out update_instances so it doesn't need a mounted widget
        table.update_instances = lambda insts, **kw: setattr(table, "instances", insts)
        return table

    def test_sort_by_name(self):
        instances = [
            make_instance(id="1", name="zebra"),
            make_instance(id="2", name="alpha"),
            make_instance(id="3", name="mango"),
        ]
        table = self._make_table_with_instances(instances)
        table.sort_by_column("name")
        assert [i.name for i in table.instances] == ["alpha", "mango", "zebra"]

    def test_sort_by_name_reverse(self):
        instances = [
            make_instance(id="1", name="alpha"),
            make_instance(id="2", name="zebra"),
        ]
        table = self._make_table_with_instances(instances)
        table.sort_by_column("name", reverse=True)
        assert table.instances[0].name == "zebra"

    def test_sort_by_status(self):
        instances = [
            make_instance(id="1", status=InstanceStatus.STOPPED),
            make_instance(id="2", status=InstanceStatus.RUNNING),
        ]
        table = self._make_table_with_instances(instances)
        table.sort_by_column("status")
        assert table.instances[0].status == InstanceStatus.RUNNING

    def test_invalid_column_noop(self):
        instances = [make_instance(id="1", name="b"), make_instance(id="2", name="a")]
        table = self._make_table_with_instances(instances)
        table.sort_by_column("nonexistent_column")
        assert [i.name for i in table.instances] == ["b", "a"]


class TestFilterInstances:
    def _make_table(self, instances):
        table = InstanceTable.__new__(InstanceTable)
        table.instances = instances
        table.resource_type = ResourceType.VPC
        captured = []
        table.update_instances = lambda insts, **kw: captured.append(list(insts))
        table._captured = captured
        return table

    def test_filter_by_name(self):
        instances = [
            make_instance(id="1", name="web-server"),
            make_instance(id="2", name="db-server"),
            make_instance(id="3", name="cache"),
        ]
        table = self._make_table(instances)
        table.filter_instances("web")
        assert len(table._captured[-1]) == 1
        assert table._captured[-1][0].name == "web-server"

    def test_filter_by_status(self):
        instances = [
            make_instance(id="1", name="a", status=InstanceStatus.RUNNING),
            make_instance(id="2", name="b", status=InstanceStatus.STOPPED),
        ]
        table = self._make_table(instances)
        table.filter_instances("stopped")
        assert len(table._captured[-1]) == 1
        assert table._captured[-1][0].name == "b"

    def test_empty_query_does_not_filter(self):
        instances = [make_instance(id="1"), make_instance(id="2")]
        table = self._make_table(instances)
        table.filter_instances("")
        assert table._captured == []  # update_instances never called

    def test_case_insensitive(self):
        instances = [make_instance(id="1", name="WebServer")]
        table = self._make_table(instances)
        table.filter_instances("WEBSERVER")
        assert len(table._captured[-1]) == 1


# ---------------------------------------------------------------------------
# Widget integration tests (mount inside a real Textual app)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_table_mounts_with_vpc_columns():
    async with TableApp().run_test() as pilot:
        table = pilot.app.query_one(InstanceTable)
        col_labels = [col.label.plain for col in table.columns.values()]
        assert "Name" in col_labels
        assert "Status" in col_labels
        assert "Zone" in col_labels


@pytest.mark.asyncio
async def test_update_instances_populates_rows():
    async with TableApp().run_test() as pilot:
        table = pilot.app.query_one(InstanceTable)
        instances = [
            make_instance(id="inst-1", name="server-1"),
            make_instance(id="inst-2", name="server-2"),
        ]
        table.update_instances(instances)
        await pilot.pause()
        assert table.row_count == 2


@pytest.mark.asyncio
async def test_update_instances_empty_shows_placeholder():
    async with TableApp().run_test() as pilot:
        table = pilot.app.query_one(InstanceTable)
        table.update_instances([])
        await pilot.pause()
        assert table.row_count == 1  # empty-state row


@pytest.mark.asyncio
async def test_set_resource_type_iks_changes_columns():
    async with TableApp().run_test() as pilot:
        table = pilot.app.query_one(InstanceTable)
        table.set_resource_type(ResourceType.IKS)
        await pilot.pause()
        col_labels = [col.label.plain for col in table.columns.values()]
        assert "Workers" in col_labels
        assert "Version" in col_labels
        assert "Status" not in col_labels


@pytest.mark.asyncio
async def test_set_resource_type_code_engine_changes_columns():
    async with TableApp().run_test() as pilot:
        table = pilot.app.query_one(InstanceTable)
        table.set_resource_type(ResourceType.CODE_ENGINE)
        await pilot.pause()
        col_labels = [col.label.plain for col in table.columns.values()]
        assert "Apps" in col_labels
        assert "Jobs" in col_labels
        assert "Builds" in col_labels
        assert "Secrets" in col_labels


@pytest.mark.asyncio
async def test_set_resource_type_same_type_is_noop():
    async with TableApp().run_test() as pilot:
        table = pilot.app.query_one(InstanceTable)
        # Add a row, then re-set the same type — columns should remain intact
        table.update_instances([make_instance()])
        await pilot.pause()
        before_count = table.row_count
        table.set_resource_type(ResourceType.VPC)  # already VPC
        await pilot.pause()
        assert table.row_count == before_count


@pytest.mark.asyncio
async def test_code_engine_update_with_project_counts():
    async with TableApp().run_test() as pilot:
        table = pilot.app.query_one(InstanceTable)
        table.set_resource_type(ResourceType.CODE_ENGINE)
        project = make_instance(id="proj-001", name="my-project")
        counts = {"proj-001": {"apps": 3, "jobs": 1, "builds": 2, "secrets": 5}}
        table.update_instances([project], project_counts=counts)
        await pilot.pause()
        assert table.row_count == 1


@pytest.mark.asyncio
async def test_iks_update_parses_workers_pools():
    async with TableApp().run_test() as pilot:
        table = pilot.app.query_one(InstanceTable)
        table.set_resource_type(ResourceType.IKS)
        cluster = make_instance(
            id="cls-001",
            name="my-cluster",
            profile="3 workers, 2 pools",
            vpc_name="IKS v1.28.5",
            zone="us-south",
        )
        table.update_instances([cluster])
        await pilot.pause()
        assert table.row_count == 1
