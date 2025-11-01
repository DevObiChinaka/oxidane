"""
Tests for the Feature model (Phase 0.5 - Task 0.5.1)

Tests cover:
- Model creation and validation
- Uniqueness constraints
- Category choices
- String representation
- Ordering
- Active/inactive filtering
- Key format validation
"""

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from subscriptions.models import Feature


@pytest.mark.django_db
class TestFeatureModel:
    """Test suite for Feature model"""
    
    def test_create_feature_success(self):
        """Test creating a valid feature"""
        feature = Feature.objects.create(
            key='view_premium_signals',
            name='View Premium Signals',
            description='Access to premium trading signals',
            category='signals',
            icon='💎',
            sort_order=1,
            is_active=True
        )
        
        assert feature.id is not None
        assert feature.key == 'view_premium_signals'
        assert feature.name == 'View Premium Signals'
        assert feature.category == 'signals'
        assert feature.icon == '💎'
        assert feature.is_active is True
        assert feature.created_at is not None
        assert feature.updated_at is not None
    
    def test_feature_key_uniqueness(self):
        """Test that feature keys must be unique"""
        Feature.objects.create(
            key='view_premium_signals',
            name='View Premium Signals',
            category='signals'
        )
        
        # Attempt to create duplicate
        # Since save() calls full_clean(), we get ValidationError instead of IntegrityError
        with pytest.raises(ValidationError):
            Feature.objects.create(
                key='view_premium_signals',
                name='Duplicate Feature',
                category='signals'
            )
    
    def test_feature_key_auto_lowercase(self):
        """Test that feature keys are automatically converted to lowercase"""
        feature = Feature.objects.create(
            key='View_Premium_SIGNALS',
            name='View Premium Signals',
            category='signals'
        )
        
        assert feature.key == 'view_premium_signals'
    
    def test_feature_key_hyphen_to_underscore(self):
        """Test that hyphens in keys are converted to underscores"""
        feature = Feature.objects.create(
            key='view-premium-signals',
            name='View Premium Signals',
            category='signals'
        )
        
        assert feature.key == 'view_premium_signals'
    
    def test_feature_key_invalid_characters(self):
        """Test that invalid characters in key raise validation error"""
        feature = Feature(
            key='view premium signals!',  # Spaces and special chars invalid
            name='View Premium Signals',
            category='signals'
        )
        
        with pytest.raises(ValidationError) as excinfo:
            feature.save()
        
        assert 'key' in excinfo.value.message_dict
    
    def test_feature_string_representation(self):
        """Test __str__ method returns icon + name"""
        feature = Feature.objects.create(
            key='telegram_vip_group',
            name='VIP Telegram Group',
            icon='👑',
            category='telegram'
        )
        
        assert str(feature) == '👑 VIP Telegram Group'
    
    def test_feature_default_values(self):
        """Test default values are applied correctly"""
        feature = Feature.objects.create(
            key='basic_feature',
            name='Basic Feature',
            category='signals'
        )
        
        assert feature.icon == '✨'  # Default icon
        assert feature.sort_order == 0  # Default sort order
        assert feature.is_active is True  # Default is_active
        assert feature.description == ''  # Default empty description
    
    def test_feature_ordering(self):
        """Test features are ordered by category, sort_order, name"""
        # Create features in random order
        Feature.objects.create(key='feature_c', name='Feature C', category='telegram', sort_order=2)
        Feature.objects.create(key='feature_a', name='Feature A', category='signals', sort_order=1)
        Feature.objects.create(key='feature_b', name='Feature B', category='signals', sort_order=1)
        Feature.objects.create(key='feature_d', name='Feature D', category='telegram', sort_order=1)
        
        features = list(Feature.objects.all())
        
        # Should be ordered by: category (signals < telegram), then sort_order, then name
        assert features[0].key == 'feature_a'  # signals, order 1, name A
        assert features[1].key == 'feature_b'  # signals, order 1, name B
        assert features[2].key == 'feature_d'  # telegram, order 1, name D
        assert features[3].key == 'feature_c'  # telegram, order 2, name C
    
    def test_filter_by_category(self):
        """Test filtering features by category"""
        Feature.objects.create(key='signal_1', name='Signal 1', category='signals')
        Feature.objects.create(key='signal_2', name='Signal 2', category='signals')
        Feature.objects.create(key='telegram_1', name='Telegram 1', category='telegram')
        Feature.objects.create(key='course_1', name='Course 1', category='courses')
        
        signals_features = Feature.objects.filter(category='signals')
        assert signals_features.count() == 2
        
        telegram_features = Feature.objects.filter(category='telegram')
        assert telegram_features.count() == 1
    
    def test_filter_active_features(self):
        """Test filtering active vs inactive features"""
        Feature.objects.create(key='active_1', name='Active 1', category='signals', is_active=True)
        Feature.objects.create(key='active_2', name='Active 2', category='signals', is_active=True)
        Feature.objects.create(key='inactive_1', name='Inactive 1', category='signals', is_active=False)
        
        active_features = Feature.objects.filter(is_active=True)
        assert active_features.count() == 2
        
        inactive_features = Feature.objects.filter(is_active=False)
        assert inactive_features.count() == 1
    
    def test_feature_category_choices(self):
        """Test all valid category choices"""
        valid_categories = ['signals', 'telegram', 'courses', 'support', 'api', 'analytics']
        
        for i, category in enumerate(valid_categories):
            feature = Feature.objects.create(
                key=f'feature_{category}',
                name=f'Feature {category}',
                category=category
            )
            assert feature.category == category
    
    def test_feature_update(self):
        """Test updating feature fields"""
        feature = Feature.objects.create(
            key='test_feature',
            name='Test Feature',
            category='signals',
            is_active=True
        )
        
        original_updated_at = feature.updated_at
        
        # Update feature
        feature.name = 'Updated Feature'
        feature.is_active = False
        feature.save()
        
        # Refresh from database
        feature.refresh_from_db()
        
        assert feature.name == 'Updated Feature'
        assert feature.is_active is False
        assert feature.updated_at > original_updated_at
    
    def test_feature_with_emoji_icons(self):
        """Test features can have various emoji icons"""
        emojis = ['📊', '💎', '👑', '🔔', '📈', '💬', '🌟', '🎓', '📚', '🏆']
        
        for i, emoji in enumerate(emojis):
            feature = Feature.objects.create(
                key=f'feature_{i}',
                name=f'Feature {i}',
                category='signals',
                icon=emoji
            )
            assert feature.icon == emoji
            assert emoji in str(feature)
    
    def test_bulk_create_features(self):
        """Test creating multiple features at once"""
        features = [
            Feature(key=f'feature_{i}', name=f'Feature {i}', category='signals')
            for i in range(5)
        ]
        
        Feature.objects.bulk_create(features)
        
        assert Feature.objects.count() == 5
    
    def test_feature_description_optional(self):
        """Test that description field is optional"""
        feature = Feature.objects.create(
            key='no_description',
            name='No Description Feature',
            category='signals'
        )
        
        assert feature.description == ''
        
        # Can also create with description
        feature2 = Feature.objects.create(
            key='with_description',
            name='With Description Feature',
            category='signals',
            description='This feature has a description'
        )
        
        assert feature2.description == 'This feature has a description'
    
    def test_feature_queryset_by_category_and_active(self):
        """Test complex filtering (category + active status)"""
        Feature.objects.create(key='s1', name='S1', category='signals', is_active=True)
        Feature.objects.create(key='s2', name='S2', category='signals', is_active=False)
        Feature.objects.create(key='t1', name='T1', category='telegram', is_active=True)
        Feature.objects.create(key='t2', name='T2', category='telegram', is_active=False)
        
        # Get active signals features
        active_signals = Feature.objects.filter(category='signals', is_active=True)
        assert active_signals.count() == 1
        assert active_signals.first().key == 's1'
        
        # Get all telegram features (active and inactive)
        telegram_all = Feature.objects.filter(category='telegram')
        assert telegram_all.count() == 2


@pytest.mark.django_db
class TestFeatureModelEdgeCases:
    """Test edge cases and boundary conditions"""
    
    def test_very_long_feature_name(self):
        """Test feature with maximum length name"""
        long_name = 'A' * 200  # Max length is 200
        feature = Feature.objects.create(
            key='long_name_feature',
            name=long_name,
            category='signals'
        )
        
        assert len(feature.name) == 200
    
    def test_feature_key_max_length(self):
        """Test feature key with maximum length"""
        long_key = 'a' * 100  # Max length is 100
        feature = Feature.objects.create(
            key=long_key,
            name='Long Key Feature',
            category='signals'
        )
        
        assert len(feature.key) == 100
    
    def test_negative_sort_order(self):
        """Test that negative sort order works (for priority features)"""
        feature = Feature.objects.create(
            key='priority_feature',
            name='Priority Feature',
            category='signals',
            sort_order=-10
        )
        
        feature2 = Feature.objects.create(
            key='normal_feature',
            name='Normal Feature',
            category='signals',
            sort_order=0
        )
        
        features = list(Feature.objects.filter(category='signals'))
        assert features[0].key == 'priority_feature'  # Negative sort order comes first
        assert features[1].key == 'normal_feature'
    
    def test_feature_unicode_in_description(self):
        """Test that Unicode characters work in description"""
        feature = Feature.objects.create(
            key='unicode_feature',
            name='Unicode Feature',
            category='signals',
            description='支持中文 • Supports emoji 🎉 • Español • العربية'
        )
        
        assert '支持中文' in feature.description
        assert '🎉' in feature.description
    
    def test_feature_deletion(self):
        """Test deleting a feature"""
        feature = Feature.objects.create(
            key='delete_me',
            name='Delete Me',
            category='signals'
        )
        
        feature_id = feature.id
        feature.delete()
        
        assert Feature.objects.filter(id=feature_id).count() == 0
    
    def test_feature_count_by_category(self):
        """Test counting features by category"""
        # Create multiple features across categories
        for i in range(3):
            Feature.objects.create(key=f'signal_{i}', name=f'Signal {i}', category='signals')
        for i in range(2):
            Feature.objects.create(key=f'telegram_{i}', name=f'Telegram {i}', category='telegram')
        for i in range(5):
            Feature.objects.create(key=f'course_{i}', name=f'Course {i}', category='courses')
        
        assert Feature.objects.filter(category='signals').count() == 3
        assert Feature.objects.filter(category='telegram').count() == 2
        assert Feature.objects.filter(category='courses').count() == 5
        assert Feature.objects.count() == 10
