from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from .models import (
    Category, Product, ProductImage, Review, ProductVariant, ProductOption
)


class CategorySerializer(serializers.ModelSerializer):
    """Serializer for Category model."""
    class Meta:
        model = Category
        fields = [
            'id', 'name', 'slug', 'description', 'parent', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ('id', 'created_at', 'updated_at')
        extra_kwargs = {
            'slug': {'read_only': True},
            'parent': {'required': False}
        }

    def validate_parent(self, value):
        """Validate that a category is not set as its own parent."""
        if self.instance and value and self.instance == value:
            raise serializers.ValidationError(
                _('A category cannot be a parent of itself.')
            )
        return value


class ProductImageSerializer(serializers.ModelSerializer):
    """Serializer for ProductImage model."""
    image_url = serializers.SerializerMethodField()
    thumbnail_url = serializers.SerializerMethodField()

    class Meta:
        model = ProductImage
        fields = ['id', 'image', 'alt_text', 'is_primary', 'position', 'image_url', 'thumbnail_url']
        read_only_fields = ('id', 'image_url', 'thumbnail_url')

    def get_image_url(self, obj):
        """Return the full URL of the image."""
        if obj.image:
            return self.context['request'].build_absolute_uri(obj.image.url)
        return None

    def get_thumbnail_url(self, obj):
        """Return the URL of the thumbnail version of the image."""
        if obj.image:
            # In a real app, you'd generate a thumbnail here
            return self.context['request'].build_absolute_uri(obj.image.url)
        return None


class ProductVariantSerializer(serializers.ModelSerializer):
    """Serializer for ProductVariant model."""
    class Meta:
        model = ProductVariant
        fields = [
            'id', 'name', 'sku', 'price', 'quantity', 'is_default',
            'created_at', 'updated_at'
        ]
        read_only_fields = ('id', 'created_at', 'updated_at')


class ProductOptionSerializer(serializers.ModelSerializer):
    """Serializer for ProductOption model."""
    class Meta:
        model = ProductOption
        fields = ['id', 'name', 'value', 'position', 'created_at']
        read_only_fields = ('id', 'created_at')


class ReviewSerializer(serializers.ModelSerializer):
    """Serializer for Review model."""
    user = serializers.StringRelatedField(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(
        source='user', read_only=True
    )
    product = serializers.StringRelatedField(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(
        source='product', read_only=True
    )

    class Meta:
        model = Review
        fields = [
            'id', 'user', 'user_id', 'product', 'product_id', 'rating', 'title',
            'comment', 'is_approved', 'is_verified_purchase', 'created_at', 'updated_at'
        ]
        read_only_fields = (
            'id', 'user', 'user_id', 'product', 'product_id', 'is_approved',
            'is_verified_purchase', 'created_at', 'updated_at'
        )

    def validate_rating(self, value):
        """Validate that rating is between 1 and 5."""
        if not 1 <= value <= 5:
            raise serializers.ValidationError(
                _('Rating must be between 1 and 5.')
            )
        return value

    def create(self, validated_data):
        """Set the user and product when creating a review."""
        request = self.context.get('request')
        product_id = self.context.get('product_id')
        
        # Check if user has already reviewed this product
        if Review.objects.filter(
            user=request.user, product_id=product_id
        ).exists():
            raise ValidationError(_('You have already reviewed this product.'))
        
        # Set user and product
        validated_data['user'] = request.user
        validated_data['product_id'] = product_id
        
        # Mark as verified purchase if user has bought the product
        from orders.models import OrderItem
        has_purchased = OrderItem.objects.filter(
            order__user=request.user,
            product_id=product_id
        ).exists()
        validated_data['is_verified_purchase'] = has_purchased
        
        return super().create(validated_data)


class ProductListSerializer(serializers.ModelSerializer):
    """Serializer for listing products (lightweight version)."""
    primary_image = serializers.SerializerMethodField()
    discount_percentage = serializers.DecimalField(
        max_digits=5, decimal_places=2, read_only=True
    )
    is_in_stock = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'price', 'compare_at_price',
            'discount_percentage', 'is_featured', 'is_active',
            'is_in_stock', 'primary_image', 'created_at'
        ]
        read_only_fields = fields

    def get_primary_image(self, obj):
        """Get the primary image URL for the product."""
        image = obj.images.filter(is_primary=True).first()
        if not image and obj.images.exists():
            image = obj.images.first()
        if image and image.image:
            request = self.context.get('request')
            return request.build_absolute_uri(image.image.url)
        return None


class ProductDetailSerializer(ProductListSerializer):
    """Detailed serializer for a single product."""
    categories = CategorySerializer(many=True, read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)
    variants = ProductVariantSerializer(many=True, read_only=True)
    options = ProductOptionSerializer(many=True, read_only=True)
    reviews = ReviewSerializer(many=True, read_only=True)
    average_rating = serializers.DecimalField(
        max_digits=3, decimal_places=2, read_only=True
    )
    review_count = serializers.IntegerField(read_only=True)
    
    class Meta(ProductListSerializer.Meta):
        fields = ProductListSerializer.Meta.fields + [
            'description', 'categories', 'images', 'variants', 'options',
            'reviews', 'average_rating', 'review_count', 'condition',
            'weight', 'height', 'width', 'length', 'seo_title',
            'seo_description', 'updated_at'
        ]
        read_only_fields = fields


class ProductCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating products."""
    class Meta:
        model = Product
        fields = [
            'name', 'description', 'price', 'compare_at_price', 'cost_per_item',
            'sku', 'barcode', 'quantity', 'track_quantity',
            'continue_selling_when_out_of_stock', 'categories', 'is_featured',
            'is_active', 'condition', 'weight', 'height', 'width', 'length',
            'seo_title', 'seo_description'
        ]
        extra_kwargs = {
            'sku': {'required': False, 'allow_blank': True},
            'barcode': {'required': False, 'allow_blank': True},
        }

    def create(self, validated_data):
        """Create a new product with the validated data."""
        categories = validated_data.pop('categories', [])
        product = Product.objects.create(**validated_data)
        product.categories.set(categories)
        return product

    def update(self, instance, validated_data):
        """Update an existing product with the validated data."""
        categories = validated_data.pop('categories', None)
        
        # Update all fields except categories
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        # Update categories if provided
        if categories is not None:
            instance.categories.set(categories)
        
        instance.save()
        return instance
