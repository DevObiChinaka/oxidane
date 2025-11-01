"""
Comprehensive test suite for TelegramGroup model (Phase 0.5, Task 0.5.7).
Tests: Group CRUD, M2M plan relationships, settings, permissions, validation.
Author: AI Assistant | Date: 2025-11-01
"""

import pytest
from decimal import Decimal
from datetime import timedelta
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone
from django.contrib.auth import get_user_model

from subscriptions.models import (
    TelegramGroup,
    SubscriptionPlan,
    Feature,
    TelegramConfiguration
)

User = get_user_model()


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def feature():
    """Create a test feature."""
    return Feature.objects.create(
        name="Premium Signals Access",
        key="premium_signals_access",
        category="signals",
        description="Access to premium trading signals"
    )


@pytest.fixture
def basic_plan(feature):
    """Create a basic subscription plan."""
    plan = SubscriptionPlan.objects.create(
        name="Basic Plan",
        slug="basic-plan",
        base_price=Decimal('29.99'),
        billing_period="monthly",
        trial_days=7,
        is_active=True,
        sort_order=1
    )
    plan.features.add(feature)
    return plan


@pytest.fixture
def premium_plan(feature):
    """Create a premium subscription plan."""
    plan = SubscriptionPlan.objects.create(
        name="Premium Plan",
        slug="premium-plan",
        base_price=Decimal('99.99'),
        billing_period="monthly",
        trial_days=14,
        is_active=True,
        sort_order=2
    )
    plan.features.add(feature)
    return plan


@pytest.fixture
def telegram_config():
    """Create Telegram configuration."""
    return TelegramConfiguration.get_instance()


# ============================================================================
# CATEGORY 1: BASIC CRUD OPERATIONS (8 tests)
# ============================================================================

@pytest.mark.django_db
class TestTelegramGroupBasicOperations:
    """Test basic CRUD operations for TelegramGroup model."""

    def test_create_telegram_group_minimal_fields(self):
        """Test creating a Telegram group with minimal required fields."""
        group = TelegramGroup.objects.create(
            name="Basic Signals Group",
            chat_id="-1001234567890",
            group_key="basic_signals"
        )
        
        assert group.id is not None
        assert group.name == "Basic Signals Group"
        assert group.chat_id == "-1001234567890"
        assert group.group_key == "basic_signals"
        assert group.is_active is True  # Default
        assert group.is_private is False  # Default
        assert group.member_count == 0  # Default
        assert group.created_at is not None
        assert group.updated_at is not None

    def test_create_telegram_group_all_fields(self, basic_plan):
        """Test creating a Telegram group with all fields."""
        group = TelegramGroup.objects.create(
            name="Premium VIP Group",
            chat_id="-1009876543210",
            group_key="premium_vip",
            description="Exclusive VIP trading signals and analysis",
            invite_link="https://t.me/+VIPSignals123",
            is_active=True,
            is_private=True,
            member_count=150,
            max_members=200,
            auto_add_enabled=True,
            auto_remove_enabled=True,
            welcome_message="Welcome to VIP Group! 🎉",
            removal_message="Your subscription has ended. Thanks!",
            notification_enabled=True,
            can_send_messages=True,
            can_add_users=True,
            can_remove_users=True,
            can_pin_messages=False,
            can_delete_messages=False,
            is_admin=False,
            last_sync_at=timezone.now(),
            sort_order=1
        )
        group.associated_plans.add(basic_plan)
        
        assert group.name == "Premium VIP Group"
        assert group.description == "Exclusive VIP trading signals and analysis"
        assert group.is_private is True
        assert group.member_count == 150
        assert group.max_members == 200
        assert group.welcome_message == "Welcome to VIP Group! 🎉"
        assert group.associated_plans.count() == 1
        assert basic_plan in group.associated_plans.all()

    def test_read_telegram_group(self):
        """Test reading a Telegram group from database."""
        group = TelegramGroup.objects.create(
            name="Test Group",
            chat_id="-1001111111111",
            group_key="test_group"
        )
        
        retrieved = TelegramGroup.objects.get(id=group.id)
        assert retrieved.name == "Test Group"
        assert retrieved.chat_id == "-1001111111111"

    def test_update_telegram_group(self):
        """Test updating a Telegram group."""
        group = TelegramGroup.objects.create(
            name="Original Name",
            chat_id="-1002222222222",
            group_key="original_group",
            member_count=50
        )
        
        group.name = "Updated Name"
        group.member_count = 75
        group.is_active = False
        group.save()
        
        retrieved = TelegramGroup.objects.get(id=group.id)
        assert retrieved.name == "Updated Name"
        assert retrieved.member_count == 75
        assert retrieved.is_active is False

    def test_delete_telegram_group(self):
        """Test deleting a Telegram group."""
        group = TelegramGroup.objects.create(
            name="Temporary Group",
            chat_id="-1003333333333",
            group_key="temp_group"
        )
        group_id = group.id
        
        group.delete()
        
        assert not TelegramGroup.objects.filter(id=group_id).exists()

    def test_list_telegram_groups(self):
        """Test listing multiple Telegram groups."""
        TelegramGroup.objects.create(
            name="Group A",
            chat_id="-1001111111111",
            group_key="group_a",
            sort_order=2
        )
        TelegramGroup.objects.create(
            name="Group B",
            chat_id="-1002222222222",
            group_key="group_b",
            sort_order=1
        )
        TelegramGroup.objects.create(
            name="Group C",
            chat_id="-1003333333333",
            group_key="group_c",
            sort_order=3
        )
        
        groups = list(TelegramGroup.objects.all())
        assert len(groups) == 3
        # Check ordering by sort_order
        assert groups[0].name == "Group B"  # sort_order=1
        assert groups[1].name == "Group A"  # sort_order=2
        assert groups[2].name == "Group C"  # sort_order=3

    def test_filter_active_groups(self):
        """Test filtering active/inactive groups."""
        TelegramGroup.objects.create(
            name="Active Group",
            chat_id="-1001111111111",
            group_key="active_group",
            is_active=True
        )
        TelegramGroup.objects.create(
            name="Inactive Group",
            chat_id="-1002222222222",
            group_key="inactive_group",
            is_active=False
        )
        
        active = TelegramGroup.objects.filter(is_active=True)
        inactive = TelegramGroup.objects.filter(is_active=False)
        
        assert active.count() == 1
        assert inactive.count() == 1
        assert active.first().name == "Active Group"

    def test_string_representation(self):
        """Test __str__ method of TelegramGroup."""
        group = TelegramGroup.objects.create(
            name="Test Group",
            chat_id="-1001234567890",
            group_key="test_group"
        )
        assert str(group) == "Test Group"


# ============================================================================
# CATEGORY 2: VALIDATION TESTS (10 tests)
# ============================================================================

@pytest.mark.django_db
class TestTelegramGroupValidation:
    """Test validation rules for TelegramGroup model."""

    def test_name_required(self):
        """Test that name is required."""
        with pytest.raises(ValidationError):
            group = TelegramGroup(
                chat_id="-1001234567890",
                group_key="test_group"
            )
            group.full_clean()

    def test_chat_id_required(self):
        """Test that chat_id is required."""
        with pytest.raises(ValidationError):
            group = TelegramGroup(
                name="Test Group",
                group_key="test_group"
            )
            group.full_clean()

    def test_group_key_required(self):
        """Test that group_key is required."""
        with pytest.raises(ValidationError):
            group = TelegramGroup(
                name="Test Group",
                chat_id="-1001234567890"
            )
            group.full_clean()

    def test_unique_name(self):
        """Test that group name must be unique."""
        TelegramGroup.objects.create(
            name="Unique Group",
            chat_id="-1001111111111",
            group_key="unique_group"
        )
        
        with pytest.raises(ValidationError):
            TelegramGroup.objects.create(
                name="Unique Group",
                chat_id="-1002222222222",
                group_key="another_key"
            )

    def test_unique_chat_id(self):
        """Test that chat_id must be unique."""
        TelegramGroup.objects.create(
            name="Group One",
            chat_id="-1001234567890",
            group_key="group_one"
        )
        
        with pytest.raises(ValidationError):
            TelegramGroup.objects.create(
                name="Group Two",
                chat_id="-1001234567890",
                group_key="group_two"
            )

    def test_unique_group_key(self):
        """Test that group_key must be unique."""
        TelegramGroup.objects.create(
            name="Group One",
            chat_id="-1001111111111",
            group_key="duplicate_key"
        )
        
        with pytest.raises(ValidationError):
            TelegramGroup.objects.create(
                name="Group Two",
                chat_id="-1002222222222",
                group_key="duplicate_key"
            )

    def test_name_max_length(self):
        """Test name field max length validation."""
        with pytest.raises(ValidationError):
            group = TelegramGroup(
                name="A" * 201,  # Max is 200
                chat_id="-1001234567890",
                group_key="test_group"
            )
            group.full_clean()

    def test_group_key_max_length(self):
        """Test group_key field max length validation."""
        with pytest.raises(ValidationError):
            group = TelegramGroup(
                name="Test Group",
                chat_id="-1001234567890",
                group_key="a" * 101  # Max is 100
            )
            group.full_clean()

    def test_chat_id_format_validation(self):
        """Test chat_id must start with minus sign (negative number)."""
        with pytest.raises(ValidationError):
            group = TelegramGroup(
                name="Invalid Chat ID",
                chat_id="1001234567890",  # Missing minus
                group_key="invalid_chat"
            )
            group.full_clean()

    def test_member_count_non_negative(self):
        """Test member_count cannot be negative."""
        with pytest.raises(ValidationError):
            group = TelegramGroup(
                name="Test Group",
                chat_id="-1001234567890",
                group_key="test_group",
                member_count=-10
            )
            group.full_clean()


# ============================================================================
# CATEGORY 3: PLAN RELATIONSHIPS (8 tests)
# ============================================================================

@pytest.mark.django_db
class TestTelegramGroupPlanRelationships:
    """Test M2M relationships between TelegramGroup and SubscriptionPlan."""

    def test_add_single_plan_to_group(self, basic_plan):
        """Test adding one plan to a group."""
        group = TelegramGroup.objects.create(
            name="Test Group",
            chat_id="-1001234567890",
            group_key="test_group"
        )
        
        group.associated_plans.add(basic_plan)
        
        assert group.associated_plans.count() == 1
        assert basic_plan in group.associated_plans.all()

    def test_add_multiple_plans_to_group(self, basic_plan, premium_plan):
        """Test adding multiple plans to one group."""
        group = TelegramGroup.objects.create(
            name="Multi-Plan Group",
            chat_id="-1001234567890",
            group_key="multi_plan"
        )
        
        group.associated_plans.add(basic_plan, premium_plan)
        
        assert group.associated_plans.count() == 2
        assert basic_plan in group.associated_plans.all()
        assert premium_plan in group.associated_plans.all()

    def test_remove_plan_from_group(self, basic_plan, premium_plan):
        """Test removing a plan from a group."""
        group = TelegramGroup.objects.create(
            name="Test Group",
            chat_id="-1001234567890",
            group_key="test_group"
        )
        group.associated_plans.add(basic_plan, premium_plan)
        
        group.associated_plans.remove(basic_plan)
        
        assert group.associated_plans.count() == 1
        assert basic_plan not in group.associated_plans.all()
        assert premium_plan in group.associated_plans.all()

    def test_clear_all_plans_from_group(self, basic_plan, premium_plan):
        """Test clearing all plans from a group."""
        group = TelegramGroup.objects.create(
            name="Test Group",
            chat_id="-1001234567890",
            group_key="test_group"
        )
        group.associated_plans.add(basic_plan, premium_plan)
        
        group.associated_plans.clear()
        
        assert group.associated_plans.count() == 0

    def test_plan_can_have_multiple_groups(self, basic_plan):
        """Test one plan can be associated with multiple groups."""
        group1 = TelegramGroup.objects.create(
            name="Group 1",
            chat_id="-1001111111111",
            group_key="group_1"
        )
        group2 = TelegramGroup.objects.create(
            name="Group 2",
            chat_id="-1002222222222",
            group_key="group_2"
        )
        
        basic_plan.telegram_groups.add(group1, group2)
        
        assert basic_plan.telegram_groups.count() == 2
        assert group1 in basic_plan.telegram_groups.all()
        assert group2 in basic_plan.telegram_groups.all()

    def test_deleting_plan_removes_m2m_relationship(self, basic_plan):
        """Test deleting a plan removes M2M relationships but keeps groups."""
        group = TelegramGroup.objects.create(
            name="Test Group",
            chat_id="-1001234567890",
            group_key="test_group"
        )
        group.associated_plans.add(basic_plan)
        
        basic_plan.delete()
        
        # Group should still exist
        assert TelegramGroup.objects.filter(id=group.id).exists()
        # But relationship is gone
        group.refresh_from_db()
        assert group.associated_plans.count() == 0

    def test_deleting_group_removes_m2m_relationship(self, basic_plan):
        """Test deleting a group removes M2M relationships but keeps plans."""
        group = TelegramGroup.objects.create(
            name="Test Group",
            chat_id="-1001234567890",
            group_key="test_group"
        )
        group.associated_plans.add(basic_plan)
        
        group.delete()
        
        # Plan should still exist
        assert SubscriptionPlan.objects.filter(id=basic_plan.id).exists()
        # But relationship is gone
        basic_plan.refresh_from_db()
        assert basic_plan.telegram_groups.count() == 0

    def test_filter_groups_by_plan(self, basic_plan, premium_plan):
        """Test filtering groups by associated plan."""
        group1 = TelegramGroup.objects.create(
            name="Basic Group",
            chat_id="-1001111111111",
            group_key="basic_group"
        )
        group2 = TelegramGroup.objects.create(
            name="Premium Group",
            chat_id="-1002222222222",
            group_key="premium_group"
        )
        group3 = TelegramGroup.objects.create(
            name="Both Plans Group",
            chat_id="-1003333333333",
            group_key="both_plans"
        )
        
        group1.associated_plans.add(basic_plan)
        group2.associated_plans.add(premium_plan)
        group3.associated_plans.add(basic_plan, premium_plan)
        
        basic_groups = TelegramGroup.objects.filter(associated_plans=basic_plan)
        premium_groups = TelegramGroup.objects.filter(associated_plans=premium_plan)
        
        assert basic_groups.count() == 2  # group1, group3
        assert premium_groups.count() == 2  # group2, group3


# ============================================================================
# CATEGORY 4: SETTINGS & PERMISSIONS (8 tests)
# ============================================================================

@pytest.mark.django_db
class TestTelegramGroupSettings:
    """Test group settings and permissions."""

    def test_default_settings_values(self):
        """Test default values for settings fields."""
        group = TelegramGroup.objects.create(
            name="Test Group",
            chat_id="-1001234567890",
            group_key="test_group"
        )
        
        assert group.auto_add_enabled is True
        assert group.auto_remove_enabled is True
        assert group.notification_enabled is True
        assert group.welcome_message == ""
        assert group.removal_message == ""

    def test_update_auto_add_setting(self):
        """Test updating auto_add_enabled setting."""
        group = TelegramGroup.objects.create(
            name="Test Group",
            chat_id="-1001234567890",
            group_key="test_group",
            auto_add_enabled=True
        )
        
        group.auto_add_enabled = False
        group.save()
        
        group.refresh_from_db()
        assert group.auto_add_enabled is False

    def test_update_welcome_message(self):
        """Test updating welcome message."""
        group = TelegramGroup.objects.create(
            name="Test Group",
            chat_id="-1001234567890",
            group_key="test_group"
        )
        
        group.welcome_message = "Welcome {{user_name}} to our group!"
        group.save()
        
        group.refresh_from_db()
        assert "{{user_name}}" in group.welcome_message

    def test_default_permissions_values(self):
        """Test default values for permission fields."""
        group = TelegramGroup.objects.create(
            name="Test Group",
            chat_id="-1001234567890",
            group_key="test_group"
        )
        
        assert group.can_send_messages is True
        assert group.can_add_users is True
        assert group.can_remove_users is True
        assert group.can_pin_messages is False
        assert group.can_delete_messages is False
        assert group.is_admin is False

    def test_update_permissions(self):
        """Test updating group permissions."""
        group = TelegramGroup.objects.create(
            name="Test Group",
            chat_id="-1001234567890",
            group_key="test_group"
        )
        
        group.can_pin_messages = True
        group.can_delete_messages = True
        group.is_admin = True
        group.save()
        
        group.refresh_from_db()
        assert group.can_pin_messages is True
        assert group.can_delete_messages is True
        assert group.is_admin is True

    def test_public_vs_private_group(self):
        """Test public and private group distinction."""
        public_group = TelegramGroup.objects.create(
            name="Public Group",
            chat_id="-1001111111111",
            group_key="public_group",
            is_private=False,
            invite_link="https://t.me/+PublicLink123"
        )
        private_group = TelegramGroup.objects.create(
            name="Private Group",
            chat_id="-1002222222222",
            group_key="private_group",
            is_private=True
        )
        
        assert public_group.is_private is False
        assert public_group.invite_link != ""
        assert private_group.is_private is True

    def test_member_limits(self):
        """Test member count and max_members."""
        group = TelegramGroup.objects.create(
            name="Limited Group",
            chat_id="-1001234567890",
            group_key="limited_group",
            member_count=80,
            max_members=100
        )
        
        assert group.member_count == 80
        assert group.max_members == 100

    def test_sync_timestamp(self):
        """Test last_sync_at timestamp."""
        group = TelegramGroup.objects.create(
            name="Test Group",
            chat_id="-1001234567890",
            group_key="test_group"
        )
        
        assert group.last_sync_at is None
        
        sync_time = timezone.now()
        group.last_sync_at = sync_time
        group.save()
        
        group.refresh_from_db()
        assert group.last_sync_at is not None


# ============================================================================
# CATEGORY 5: HELPER METHODS (8 tests)
# ============================================================================

@pytest.mark.django_db
class TestTelegramGroupMethods:
    """Test helper methods on TelegramGroup model."""

    def test_get_member_count_method(self):
        """Test getting current member count."""
        group = TelegramGroup.objects.create(
            name="Test Group",
            chat_id="-1001234567890",
            group_key="test_group",
            member_count=150
        )
        
        assert group.get_member_count() == 150

    def test_can_auto_add_method(self):
        """Test checking if auto-add is enabled."""
        group1 = TelegramGroup.objects.create(
            name="Auto Add Group",
            chat_id="-1001111111111",
            group_key="auto_add",
            auto_add_enabled=True,
            is_active=True
        )
        group2 = TelegramGroup.objects.create(
            name="Manual Add Group",
            chat_id="-1002222222222",
            group_key="manual_add",
            auto_add_enabled=False,
            is_active=True
        )
        group3 = TelegramGroup.objects.create(
            name="Inactive Group",
            chat_id="-1003333333333",
            group_key="inactive",
            auto_add_enabled=True,
            is_active=False
        )
        
        assert group1.can_auto_add() is True
        assert group2.can_auto_add() is False
        assert group3.can_auto_add() is False  # Inactive

    def test_can_auto_remove_method(self):
        """Test checking if auto-remove is enabled."""
        group = TelegramGroup.objects.create(
            name="Test Group",
            chat_id="-1001234567890",
            group_key="test_group",
            auto_remove_enabled=True,
            is_active=True
        )
        
        assert group.can_auto_remove() is True

    def test_is_accessible_to_plan_method(self, basic_plan, premium_plan):
        """Test checking if a plan can access this group."""
        group = TelegramGroup.objects.create(
            name="Premium Group",
            chat_id="-1001234567890",
            group_key="premium_group"
        )
        group.associated_plans.add(premium_plan)
        
        assert group.is_accessible_to_plan(premium_plan) is True
        assert group.is_accessible_to_plan(basic_plan) is False

    def test_has_capacity_method(self):
        """Test checking if group has capacity for new members."""
        group1 = TelegramGroup.objects.create(
            name="Full Group",
            chat_id="-1001111111111",
            group_key="full_group",
            member_count=100,
            max_members=100
        )
        group2 = TelegramGroup.objects.create(
            name="Available Group",
            chat_id="-1002222222222",
            group_key="available_group",
            member_count=50,
            max_members=100
        )
        group3 = TelegramGroup.objects.create(
            name="Unlimited Group",
            chat_id="-1003333333333",
            group_key="unlimited_group",
            member_count=500,
            max_members=None
        )
        
        assert group1.has_capacity() is False
        assert group2.has_capacity() is True
        assert group3.has_capacity() is True  # No limit

    def test_update_member_count_method(self):
        """Test updating member count with sync timestamp."""
        group = TelegramGroup.objects.create(
            name="Test Group",
            chat_id="-1001234567890",
            group_key="test_group",
            member_count=100
        )
        
        old_sync = group.last_sync_at
        group.update_member_count(150)
        
        assert group.member_count == 150
        assert group.last_sync_at is not None
        assert group.last_sync_at != old_sync

    def test_get_welcome_message_method(self):
        """Test getting formatted welcome message."""
        group = TelegramGroup.objects.create(
            name="Test Group",
            chat_id="-1001234567890",
            group_key="test_group",
            welcome_message="Welcome {{user_name}} to {{group_name}}!"
        )
        
        message = group.get_welcome_message(user_name="John")
        assert "John" in message
        assert "Test Group" in message

    def test_get_removal_message_method(self):
        """Test getting formatted removal message."""
        group = TelegramGroup.objects.create(
            name="Test Group",
            chat_id="-1001234567890",
            group_key="test_group",
            removal_message="Goodbye {{user_name}}, thanks for being part of {{group_name}}!"
        )
        
        message = group.get_removal_message(user_name="Jane")
        assert "Jane" in message
        assert "Test Group" in message


# ============================================================================
# CATEGORY 6: EDGE CASES & SPECIAL SCENARIOS (6 tests)
# ============================================================================

@pytest.mark.django_db
class TestTelegramGroupEdgeCases:
    """Test edge cases and special scenarios."""

    def test_group_with_no_plans(self):
        """Test creating a group without associated plans."""
        group = TelegramGroup.objects.create(
            name="No Plans Group",
            chat_id="-1001234567890",
            group_key="no_plans"
        )
        
        assert group.associated_plans.count() == 0

    def test_group_with_empty_description(self):
        """Test group with blank description."""
        group = TelegramGroup.objects.create(
            name="Test Group",
            chat_id="-1001234567890",
            group_key="test_group",
            description=""
        )
        
        assert group.description == ""

    def test_group_with_very_long_description(self):
        """Test group with maximum length description."""
        long_desc = "A" * 1000
        group = TelegramGroup.objects.create(
            name="Test Group",
            chat_id="-1001234567890",
            group_key="test_group",
            description=long_desc
        )
        
        assert len(group.description) == 1000

    def test_multiple_groups_same_sort_order(self):
        """Test multiple groups can have the same sort_order."""
        group1 = TelegramGroup.objects.create(
            name="Group 1",
            chat_id="-1001111111111",
            group_key="group_1",
            sort_order=1
        )
        group2 = TelegramGroup.objects.create(
            name="Group 2",
            chat_id="-1002222222222",
            group_key="group_2",
            sort_order=1
        )
        
        assert group1.sort_order == group2.sort_order == 1

    def test_group_timestamps_auto_update(self):
        """Test that updated_at automatically updates on save."""
        group = TelegramGroup.objects.create(
            name="Test Group",
            chat_id="-1001234567890",
            group_key="test_group"
        )
        
        original_updated = group.updated_at
        
        # Wait a moment and update
        import time
        time.sleep(0.1)
        
        group.name = "Updated Name"
        group.save()
        
        assert group.updated_at > original_updated

    def test_deactivate_group_with_plans(self, basic_plan):
        """Test deactivating a group that has associated plans."""
        group = TelegramGroup.objects.create(
            name="Active Group",
            chat_id="-1001234567890",
            group_key="active_group",
            is_active=True
        )
        group.associated_plans.add(basic_plan)
        
        group.is_active = False
        group.save()
        
        # Group should be inactive but plans still associated
        assert group.is_active is False
        assert group.associated_plans.count() == 1


# ============================================================================
# SUMMARY
# ============================================================================
"""
TELEGRAM GROUP MODEL TEST SUMMARY:
==================================

CATEGORY 1: Basic CRUD Operations (8 tests)
- Create with minimal/all fields
- Read, update, delete operations
- List and filter groups
- String representation

CATEGORY 2: Validation Tests (10 tests)
- Required field validation
- Unique constraints (name, chat_id, group_key)
- Max length validation
- Format validation (chat_id, member_count)

CATEGORY 3: Plan Relationships (8 tests)
- M2M add/remove operations
- Multiple plans per group
- Multiple groups per plan
- Cascade behavior on deletion
- Filtering by relationships

CATEGORY 4: Settings & Permissions (8 tests)
- Default settings values
- Auto-add/remove settings
- Welcome/removal messages
- Permission flags
- Public vs private groups
- Member limits and sync

CATEGORY 5: Helper Methods (8 tests)
- get_member_count()
- can_auto_add()
- can_auto_remove()
- is_accessible_to_plan()
- has_capacity()
- update_member_count()
- get_welcome_message()
- get_removal_message()

CATEGORY 6: Edge Cases (6 tests)
- Groups without plans
- Empty/long descriptions
- Same sort_order
- Timestamp auto-update
- Deactivate with plans

TOTAL: 48 TESTS
Target: 40+ tests ✅
Coverage: All major functionality ✅
"""
