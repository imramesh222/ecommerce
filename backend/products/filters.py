import django_filters
from django.db.models import Q
from .models import Product, Category


class ProductFilter(django_filters.FilterSet):
    """
    FilterSet for Product model with advanced filtering options.
    """
    # Basic filters
    name = django_filters.CharFilter(lookup_expr='icontains')
    description = django_filters.CharFilter(lookup_expr='icontains')
    sku = django_filters.CharFilter(lookup_expr='iexact')
    barcode = django_filters.CharFilter(lookup_expr='iexact')
    
    # Price range filters
    min_price = django_filters.NumberFilter(field_name='price', lookup_expr='gte')
    max_price = django_filters.NumberFilter(field_name='price', lookup_expr='lte')
    
    # Category filters
    category = django_filters.CharFilter(method='filter_by_category')
    category_id = django_filters.NumberFilter(field_name='categories__id')
    
    # Stock status filter
    in_stock = django_filters.BooleanFilter(method='filter_in_stock')
    
    # Featured and active filters
    is_featured = django_filters.BooleanFilter(field_name='is_featured')
    is_active = django_filters.BooleanFilter(field_name='is_active')
    
    # Condition filter
    condition = django_filters.ChoiceFilter(
        field_name='condition',
        choices=Product.CONDITION_CHOICES
    )
    
    # Rating filter
    min_rating = django_filters.NumberFilter(method='filter_by_rating')
    
    # Date range filters
    created_after = django_filters.DateFilter(field_name='created_at', lookup_expr='gte')
    created_before = django_filters.DateFilter(field_name='created_at', lookup_expr='lte')
    
    # Search filter (combines multiple fields)
    search = django_filters.CharFilter(method='filter_search')
    
    class Meta:
        model = Product
        fields = {
            'name': ['exact', 'icontains'],
            'price': ['exact', 'lt', 'gt', 'lte', 'gte'],
            'quantity': ['exact', 'lt', 'gt', 'lte', 'gte'],
            'is_active': ['exact'],
            'is_featured': ['exact'],
            'condition': ['exact'],
        }
    
    def filter_by_category(self, queryset, name, value):
        """
        Filter products by category slug or name.
        """
        if not value:
            return queryset
            
        # Try to find category by slug first, then by name
        category_qs = Category.objects.filter(
            Q(slug=value) | Q(name__iexact=value)
        )
        
        if not category_qs.exists():
            return queryset.none()
            
        # Get all descendant categories if include_children is True
        include_children = self.request.query_params.get('include_children', 'true').lower() == 'true'
        
        if include_children:
            categories = []
            for category in category_qs:
                categories.extend(category.get_descendants(include_self=True))
            
            # Remove duplicates while preserving order
            seen = set()
            unique_categories = []
            for cat in categories:
                if cat.id not in seen:
                    seen.add(cat.id)
                    unique_categories.append(cat)
            
            category_ids = [cat.id for cat in unique_categories]
        else:
            category_ids = [cat.id for cat in category_qs]
        
        return queryset.filter(categories__in=category_ids).distinct()
    
    def filter_in_stock(self, queryset, name, value):
        """
        Filter products by in-stock status.
        """
        if value is None:
            return queryset
            
        if value:
            # Products that are either not tracking quantity, or have quantity > 0,
            # or have continue_selling_when_out_of_stock=True
            return queryset.filter(
                Q(track_quantity=False) | 
                (Q(track_quantity=True) & Q(quantity__gt=0)) |
                (Q(track_quantity=True) & Q(continue_selling_when_out_of_stock=True))
            )
        else:
            # Products that track quantity and have quantity <= 0
            return queryset.filter(
                track_quantity=True,
                quantity__lte=0,
                continue_selling_when_out_of_stock=False
            )
    
    def filter_by_rating(self, queryset, name, value):
        """
        Filter products by minimum average rating.
        """
        if not value:
            return queryset
            
        try:
            min_rating = float(value)
            if not (0 <= min_rating <= 5):
                return queryset.none()
                
            # Annotate with average rating and filter
            return queryset.annotate(
                avg_rating=Avg('reviews__rating')
            ).filter(
                avg_rating__gte=min_rating,
                reviews__is_approved=True
            ).distinct()
            
        except (ValueError, TypeError):
            return queryset.none()
    
    def filter_search(self, queryset, name, value):
        """
        Combined search across multiple fields.
        """
        if not value:
            return queryset
            
        # Split search terms by spaces and remove empty strings
        search_terms = [term.strip() for term in value.split() if term.strip()]
        
        if not search_terms:
            return queryset
            
        # Start with an empty Q object
        search_query = Q()
        
        # Build a query that searches across multiple fields
        for term in search_terms:
            search_query |= (
                Q(name__icontains=term) |
                Q(description__icontains=term) |
                Q(short_description__icontains=term) |
                Q(sku__iexact=term) |
                Q(barcode__iexact=term) |
                Q(categories__name__icontains=term) |
                Q(brand__icontains=term) |
                Q(condition__icontains=term)
            )
        
        return queryset.filter(search_query).distinct()


class CategoryFilter(django_filters.FilterSet):
    """
    FilterSet for Category model.
    """
    name = django_filters.CharFilter(lookup_expr='icontains')
    parent = django_filters.NumberFilter(field_name='parent__id')
    parent_slug = django_filters.CharFilter(field_name='parent__slug')
    is_active = django_filters.BooleanFilter(field_name='is_active')
    
    class Meta:
        model = Category
        fields = ['name', 'parent', 'parent_slug', 'is_active']
