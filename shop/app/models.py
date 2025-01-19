

from django.db import models
from django.forms import ValidationError


class PricingRule(models.TextChoices):
    DISCOUNT_10 = 'discount_10', "Скидка 10%"
    DISCOUNT_15 = 'discount_15', "Скидка 15%"
    FREE_EVERY_5TH = 'free_every_5th', "Каждый 5-й товар бесплатный"


class Category(models.Model):
    name = models.CharField(max_length=255)
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children'
    )

    def get_descendants(self):
        """Возвращает всех потомков категории (включая подкатегории всех уровней)."""
        descendants = set()
        subcategories = self.children.all()
        for subcategory in subcategories:
            descendants.add(subcategory)
            descendants.update(subcategory.get_descendants())
        return descendants

    def save(self, *args, **kwargs):
        # Проверяем уровень вложенности
        level = self.get_nesting_level()
        if level > 10:
            raise ValidationError(
                f"Нельзя создать вложенность более 10 уровней, текущий уровень: {level}")
        super().save(*args, **kwargs)

    def get_nesting_level(self):
        """Рекурсивно вычисляет уровень вложенности."""
        level = 0
        parent = self.parent
        while parent:
            level += 1
            parent = parent.parent
        return level

    def __str__(self):
        return self.name


class Product(models.Model):
    title = models.CharField(max_length=255)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    price = models.DecimalField('Price', max_digits=2, decimal_places=2)

    def get_price(self):
        """Возвращает цену товара."""
        return self.price

    def __str__(self):
        return f"{self.title} - {self.price}₽"


class GroupProduct(Product):
    products = models.ManyToManyField(
        Product, related_name='groups', blank=True)
    pricing_rule = models.CharField(
        max_length=50,
        choices=PricingRule.choices,
        default=PricingRule.DISCOUNT_10,
    )

    def get_price(self):
        """Формирует цену группы товаров."""
        included_products = list(self.products.all())
        total_price = sum(product.get_price() for product in included_products)

        match self.pricing_rule:
            case self.PricingRule.DISCOUNT_10:
                return total_price * 0.9  # Скидка 10%
            case self.PricingRule.DISCOUNT_15:
                return total_price * 0.85  # Скидка 15%
            case self.PricingRule.FREE_EVERY_5TH:
                sorted_products = sorted(
                    included_products, key=lambda x: x.get_price())
                # Каждый 5-й товар бесплатный
                free_count = len(sorted_products) // 5
                free_total = sum(product.get_price()
                                 for product in sorted_products[:free_count])
                return total_price - free_total

        return total_price

    def __str__(self):
        return f"Группа: {self.title} - {self.get_price()}₽"
