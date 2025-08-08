from django.db import models


class MemberQuerySet(models.QuerySet):
    def top_active(self):
        return self.annotate(
            active_loans=models.Count("loans", models.Q(loans__is_returned=False))
        ).select_related("user").order_by('-active_loans')[:5]


class MemberManager(models.Manager):
    def get_queryset(self):
        return MemberQuerySet(self.model, using=self._db)
    
    def top_active(self):
        return self.get_queryset().top_active()
