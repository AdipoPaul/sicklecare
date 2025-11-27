from .models import Resource

def get_resources_by_keyword(keyword, language="English"):
    return Resource.objects.filter(
        category__icontains=keyword.lower(),
        language=language
    )