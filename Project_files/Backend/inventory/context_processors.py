from django.db.models import Q, F
from .models import Product


def alert_count(request):

    if not request.user.is_authenticated:
        return {}

    count = Product.objects.filter(
        Q(inventory_level=0) |
        Q(predicted_demand__gt=F("inventory_level")) |
        Q(inventory_level__gt=0, inventory_level__lt=25)
    ).count()

    return {
        "total_alerts": count
    }