
from django.db import models
from django.forms import ValidationError


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
        subcategories = self.subcategories.all()
        for subcategory in subcategories:
            descendants.add(subcategory)
            descendants.update(subcategory.get_descendants())
        return descendants

    def save(self, *args, **kwargs):
        # Проверяем уровень вложенности
        level = self.get_nesting_level()
        if level > 10:
            raise ValidationError(f"Нельзя создать вложенность более 10 уровней, текущий уровень: {level}")
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


class GroupProduct(models.Model):
    title = models.CharField(max_length=255)
    products = models.ManyToManyField(Product)


    def calc_price(self):
        pass



