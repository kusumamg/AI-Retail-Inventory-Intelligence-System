from django.db import models
from users.models import Store


# ============================================================
# PRODUCT / INVENTORY
# ============================================================

class Product(models.Model):

    product_id = models.CharField(
        max_length=20
    )

    store = models.ForeignKey(
        Store,
        on_delete=models.CASCADE,
        related_name="products"
    )

    category = models.CharField(
        max_length=100
    )

    subcategory = models.CharField(
    max_length=100,
    default=""
    )

    region = models.CharField(
        max_length=100
    )

    inventory_level = models.PositiveIntegerField(
        default=0
    )

    price = models.FloatField(
        default=0
    )

    discount = models.FloatField(
        default=0
    )

    weather_condition = models.CharField(
        max_length=50
    )

    holiday_promotion = models.BooleanField(
        default=False
    )

    competitor_pricing = models.FloatField(
        default=0
    )

    seasonality = models.CharField(
        max_length=50
    )

    predicted_demand = models.FloatField(
    null=True,
    blank=True,
    default=None
)

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:

        ordering = ["product_id"]

        constraints = [
            models.UniqueConstraint(
                fields=["store", "product_id"],
                name="unique_product_per_store"
            )
        ]

    def __str__(self):
        return f"{self.product_id} - {self.category}"

    @property
    def stock_status(self):

        if self.inventory_level == 0:
            return "OUT_OF_STOCK"

        elif self.inventory_level < 25:
            return "LOW_STOCK"

        return "IN_STOCK"