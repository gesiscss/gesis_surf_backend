# Monthly Elasticsearch Index Rotation for Addons - Implementation Guide

**Step-by-Step Guide for Creating Addons with Automatic Monthly Index Rotation**

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Step-by-Step Implementation](#step-by-step-implementation)
3. [Example: Creating a New Social Media Addon](#example-creating-a-new-social-media-addon)
4. [Testing Your Implementation](#testing-your-implementation)
5. [Deployment](#deployment)
6. [Troubleshooting](#troubleshooting)

---

## Quick Start

### What You Get

- ✅ **Automatic Monthly Indexes**: `your_addon_2025_11`, `your_addon_2025_12`, etc.
- ✅ **Migration Integration**: Indexes created during `python manage.py migrate`
- ✅ **Zero Configuration**: Works automatically after setup
- ✅ **Production Ready**: Handles month transitions seamlessly

### Architecture Overview

```
API Request → Django Serializer → BaseIndex.save() → Monthly Elasticsearch Index
                                      ↓
                            Auto-creates index if missing
```

---

## Step-by-Step Implementation

### Step 1: Create Your Index Document Class

Create your index definition file:

```bash
# Create file: app/core/indexes/your_addon_index.py
```

```python
# app/core/indexes/your_addon_index.py
"""
Index document for your addon data
"""

from elasticsearch_dsl import Date, Keyword, Text, Object
from .base_index import BaseIndex


class YourAddonIndex(BaseIndex):
    """
    Elasticsearch document for your addon data

    This will create monthly indexes like: your_addon_2025_11, your_addon_2025_12
    """

    # Define your data fields
    user_id = Keyword()  # For exact matching
    content = Text()  # For full-text search
    category = Keyword()  # For filtering/aggregations
    timestamp = Date()  # For time-based queries
    metadata = Object()  # For complex nested data (optional)

    class Index:
        """
        Index configuration
        """

        name = "your_addon"  # Base name - becomes your_addon_2025_11, etc.
```

### Step 2: Create Addon Directory Structure

Create your addon directory:

```bash
mkdir -p app/addons/your_addon
touch app/addons/your_addon/__init__.py
```

Your structure should look like:

```
app/addons/
├── __init__.py
├── apps.py
├── chatgpt/          # Existing addon
├── twitter/          # Existing addon
└── your_addon/       # Your new addon
    ├── __init__.py
    ├── serializers.py
    ├── views.py
    └── urls.py
```

### Step 3: Create Serializer

```python
# app/addons/your_addon/serializers.py
"""
Serializers for your addon with automatic monthly indexing
"""

from core.indexes.your_addon_index import YourAddonIndex
from elasticsearch.exceptions import TransportError
from rest_framework import serializers


class YourAddonDataSerializer(serializers.Serializer):
    """
    Serializer for your addon data with automatic monthly indexing
    """

    user_id = serializers.CharField(max_length=100)
    content = serializers.CharField()
    category = serializers.CharField(max_length=50)
    timestamp = serializers.DateTimeField()
    metadata = serializers.JSONField(required=False, default=dict)

    def create(self, validated_data: dict) -> dict:
        """
        Create new document in current month's Elasticsearch index
        """
        try:
            doc = YourAddonIndex(**validated_data)
            doc.save()  # Automatically uses monthly index (e.g., your_addon_2025_11)

            return {
                **validated_data,
                "index_name": doc.get_current_index(),
                "document_id": doc.meta.id,
            }
        except TransportError as error:
            raise serializers.ValidationError(
                {"elasticsearch_error": str(error)}
            ) from error

    def update(self, instance: object, validated_data: dict) -> object:
        """
        Update existing document (implement if needed)
        """
        raise NotImplementedError("Update not implemented for this addon")
```

### Step 4: Create Views

```python
# app/addons/your_addon/views.py
"""
API views for your addon
"""

from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import YourAddonDataSerializer


class YourAddonDataView(APIView):
    """
    API endpoint for your addon data with monthly Elasticsearch indexing
    """

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = YourAddonDataSerializer

    def post(self, request) -> Response:
        """
        Create new data entry in current month's Elasticsearch index
        """
        serializer = self.serializer_class(data=request.data)

        if serializer.is_valid():
            result = serializer.save()
            return Response(
                {
                    "success": True,
                    "data": result,
                    "message": f"Data saved to index: {result['index_name']}",
                },
                status=status.HTTP_201_CREATED,
            )

        return Response(
            {"success": False, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )

    def get(self, request) -> Response:
        """
        Optional: Add search/retrieve functionality
        """
        return Response(
            {
                "message": "Search functionality not implemented yet",
                "current_index": YourAddonIndex.get_current_index(),
            }
        )
```

### Step 5: Create URL Configuration

```python
# app/addons/your_addon/urls.py
"""
URL configuration for your addon
"""

from django.urls import path
from . import views

app_name = "your_addon"

urlpatterns = [
    path("data/", views.YourAddonDataView.as_view(), name="data"),
]
```

### Step 6: Register Your Index in Apps Configuration

**CRITICAL STEP**: Add your index to the migration system:

```python
# app/addons/apps.py
"""
App configuration with migration-based index creation
"""

from datetime import datetime
from django.apps import AppConfig
from django.db.models.signals import post_migrate
from django.dispatch import receiver
from elasticsearch_dsl import connections


class AddonsConfig(AppConfig):
    """Addons app configuration with migration support"""

    default_auto_field = "django.db.models.BigAutoField"
    name = "addons"

    def ready(self) -> None:
        """Set up Elasticsearch connections and migration-based index creation"""

        connections.create_connection(
            alias="default",
            hosts=["http://elasticsearch:9200"],
        )

        # Import ALL index classes - MANUALLY MAINTAINED LIST
        from core.indexes.chatgpt_index import ChatGPTIndex
        from core.indexes.twitter_index import TwitterIndex
        from core.indexes.your_addon_index import YourAddonIndex  # ADD YOUR INDEX HERE

        @receiver(post_migrate)
        def create_elasticsearch_indices(sender, **kwargs):
            """
            Create monthly Elasticsearch indices during migration
            """
            # ADD YOUR INDEX TO THIS LIST
            index_classes = [
                ChatGPTIndex,
                TwitterIndex,
                YourAddonIndex,  # ← ADD YOUR NEW INDEX HERE
                # Add more indexes here as you create them
            ]

            current_date = datetime.now()
            print(f"Creating monthly indexes for {len(index_classes)} index types...")

            for index_class in index_classes:
                print(f"Setting up monthly indices for: {index_class.__name__}")

                # Create current month's index
                index_class.create_current_month_index()

                # Pre-create next month's index for smooth transitions
                next_month_date = self._get_next_month(current_date)
                next_index_name = index_class.get_time_based_index_name(next_month_date)

                next_index_template = index_class._index.clone(name=next_index_name)
                if not next_index_template.exists():
                    next_index_template.create()
                    print(f"Pre-created next month's index: {next_index_name}")
                else:
                    print(f"Next month's index already exists: {next_index_name}")

            print("Elasticsearch monthly index setup completed!")

    def _get_next_month(self, date_obj: datetime) -> datetime:
        """Calculate the first day of the next month"""
        if date_obj.month == 12:
            return date_obj.replace(year=date_obj.year + 1, month=1, day=1)
        else:
            return date_obj.replace(month=date_obj.month + 1, day=1)
```

### Step 7: Add to Main URL Configuration

```python
# app/app/urls.py
"""
Main URL configuration - ADD YOUR ADDON
"""

from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/schema/", SpectacularAPIView.as_view(), name="api-schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="api-schema"),
        name="api-docs",
    ),
    # Existing endpoints
    path("api/user/", include("user.urls")),
    path("api/window/", include("window.urls")),
    path("api/tab/", include("tab.urls")),
    path("api/domain/", include("domain.urls")),
    path("api/host/", include("host.urls")),
    path("api/globalsession/", include("globalsession.urls")),
    path("api/clicks/", include("clicks.urls")),
    path("api/scrolls/", include("scrolls.urls")),
    path("api/twitter/", include("addons.twitter.urls")),
    path("api/chatgpt/", include("addons.chatgpt.urls")),
    # ADD YOUR NEW ADDON
    path("api/your-addon/", include("addons.your_addon.urls")),
]
```

### Step 8: Run Migration to Create Indexes

```bash
# Create your monthly indexes
python manage.py migrate
```

Expected output:

```
Operations to perform:
  Apply all migrations: (existing apps)
Running migrations:
  No new migrations to apply.
Creating monthly indexes for 3 index types...
Setting up monthly indices for: ChatGPTIndex
Created monthly index: chatgpt_index_2025_11
Pre-created next month's index: chatgpt_index_2025_12
Setting up monthly indices for: TwitterIndex
Created monthly index: twitter_index_2025_11
Pre-created next month's index: twitter_index_2025_12
Setting up monthly indices for: YourAddonIndex
Created monthly index: your_addon_2025_11
Pre-created next month's index: your_addon_2025_12
Elasticsearch monthly index setup completed!
```

---

## Example: Creating a LinkedIn Addon

Let's walk through creating a real LinkedIn data addon:

### 1. Create Index

```python
# app/core/indexes/linkedin_index.py
"""
LinkedIn data index with monthly rotation
"""

from elasticsearch_dsl import Date, Keyword, Text
from .base_index import BaseIndex


class LinkedInIndex(BaseIndex):
    """LinkedIn posts and interactions"""

    post_id = Keyword()
    author_id = Keyword()
    content = Text()
    post_type = Keyword()  # post, comment, like, share
    engagement_count = Integer()
    timestamp = Date()

    class Index:
        name = "linkedin_data"
```

### 2. Create Serializer

```python
# app/addons/linkedin/serializers.py
"""
LinkedIn addon serializers
"""

from core.indexes.linkedin_index import LinkedInIndex
from rest_framework import serializers
from elasticsearch.exceptions import TransportError


class LinkedInDataSerializer(serializers.Serializer):
    """LinkedIn data with monthly indexing"""

    post_id = serializers.CharField(max_length=100)
    author_id = serializers.CharField(max_length=100)
    content = serializers.CharField()
    post_type = serializers.ChoiceField(choices=["post", "comment", "like", "share"])
    engagement_count = serializers.IntegerField(default=0)
    timestamp = serializers.DateTimeField()

    def create(self, validated_data: dict) -> dict:
        """Save to monthly LinkedIn index"""
        try:
            doc = LinkedInIndex(**validated_data)
            doc.save()

            return {
                **validated_data,
                "index_name": doc.get_current_index(),  # linkedin_data_2025_11
                "document_id": doc.meta.id,
            }
        except TransportError as error:
            raise serializers.ValidationError({"linkedin_error": str(error)}) from error
```

### 3. Add to Apps Configuration

```python
# app/addons/apps.py - ADD TO EXISTING FILE

# Import your new index
from core.indexes.linkedin_index import LinkedInIndex

# Add to index_classes list
index_classes = [
    ChatGPTIndex,
    TwitterIndex,
    YourAddonIndex,
    LinkedInIndex,  # ← ADD THIS
]
```

### 4. Test Your LinkedIn Addon

```bash
# Test API call
curl -X POST http://localhost:8000/api/linkedin/data/ \
  -H "Authorization: Token your_token" \
  -H "Content-Type: application/json" \
  -d '{
    "post_id": "post123",
    "author_id": "user456",
    "content": "Great insights on AI!",
    "post_type": "post",
    "engagement_count": 42,
    "timestamp": "2025-11-18T10:00:00Z"
  }'
```

---

## Testing Your Implementation

### Test Index Creation

```bash
# Django shell
python manage.py shell
```

```bash
# Check if indexes were created
from elasticsearch_dsl import connections
es = connections.get_connection()

# List all your addon indexes
indices = es.cat.indices(format="json")
for idx in indices:
    if "your_addon" in idx["index"]:
        print(f"Index: {idx['index']}, Documents: {idx['docs.count']}")
```

### Test Data Saving

```python
# Test in Django shell
from addons.your_addon.serializers import YourAddonDataSerializer
from datetime import datetime

data = {
    "user_id": "test123",
    "content": "Test content",
    "category": "test",
    "timestamp": datetime.now(),
    "metadata": {"source": "test"},
}

serializer = YourAddonDataSerializer(data=data)
if serializer.is_valid():
    result = serializer.save()
    print(f"Saved to: {result['index_name']}")
    print(f"Document ID: {result['document_id']}")
else:
    print("Errors:", serializer.errors)
```

### Verify Monthly Rotation

```python
# Test different months
from core.indexes.your_addon_index import YourAddonIndex
from datetime import datetime

# November index
nov_index = YourAddonIndex.get_time_based_index_name(datetime(2025, 11, 1))
print(nov_index)  # your_addon_2025_11

# December index
dec_index = YourAddonIndex.get_time_based_index_name(datetime(2025, 12, 1))
print(dec_index)  # your_addon_2025_12
```

---

## Deployment

### Production Checklist

1. **Update Environment Variables**:

   ```bash
   # Set your Elasticsearch host
   ELASTICSEARCH_HOSTS=http://your-production-es:9200
   ```

2. **Run Migration**:

   ```bash
   python manage.py migrate
   ```

3. **Verify Indexes Created**:
   ```bash
   curl "http://your-es-host:9200/_cat/indices?v" | grep your_addon
   ```

### Deployment Commands

```bash
# Standard deployment process
python manage.py migrate                    # Creates indexes
python manage.py collectstatic --noinput   # Static files
python manage.py check --deploy           # Security check

# Start your application
gunicorn app.wsgi:application
```

---

## Troubleshooting

### Common Issues

#### Issue 1: "Index not found" Error

```
elasticsearch.exceptions.NotFoundError: 404 - index_not_found_exception
```

**Solutions**:

1. Run migration: `python manage.py migrate`
2. Check if you added your index to `apps.py` index_classes list
3. Verify Elasticsearch is running: `curl http://localhost:9200/_cluster/health`

#### Issue 2: Import Error

```
ImportError: cannot import name 'YourAddonIndex'
```

**Solutions**:

1. Check file path: `app/core/indexes/your_addon_index.py` exists
2. Verify class name matches import in `apps.py`
3. Check for Python syntax errors in your index file

#### Issue 3: Data Not Appearing

```
API returns success but no data in Elasticsearch
```

**Solutions**:

1. Check index name: `YourAddonIndex.get_current_index()`
2. Verify serializer calls `doc.save()` without parameters
3. Check Elasticsearch logs for errors

#### Issue 4: Month Transition Problems

```
December data still going to November index
```

**Solutions**:

1. Check server date/time
2. Restart Django application to clear any cached connections
3. Run migration again to ensure December index exists

### Debug Commands

```python
# Check current index name
from core.indexes.your_addon_index import YourAddonIndex

print("Current index:", YourAddonIndex.get_current_index())

# Check if index exists
from elasticsearch_dsl import connections

es = connections.get_connection()
index_exists = es.indices.exists(index="your_addon_2025_11")
print(f"Index exists: {index_exists}")

# Count documents in index
count = es.count(index="your_addon_2025_11")
print(f"Documents in index: {count['count']}")

# Search recent documents
search = es.search(
    index="your_addon_*",
    body={"query": {"match_all": {}}, "sort": [{"timestamp": "desc"}], "size": 5},
)
print("Recent documents:", search["hits"]["hits"])
```

---

## Summary Checklist

When creating a new addon, ensure you complete ALL these steps:

- [ ] **Step 1**: Create index class in `app/core/indexes/your_addon_index.py`
- [ ] **Step 2**: Create addon directory structure `app/addons/your_addon/`
- [ ] **Step 3**: Create serializer with monthly indexing
- [ ] **Step 4**: Create API views
- [ ] **Step 5**: Create URL configuration
- [ ] **Step 6**: ⚠️ **CRITICAL**: Add your index to `apps.py` index_classes list
- [ ] **Step 7**: Add URL to main `app/urls.py`
- [ ] **Step 8**: Run `python manage.py migrate`
- [ ] **Step 9**: Test API endpoints
- [ ] **Step 10**: Verify data in Elasticsearch

### Quick Reference

**Current month index name**: `your_addon_2025_11`
**API endpoint**: `POST /api/your-addon/data/`
**Migration command**: `python manage.py migrate`
**Index list location**: `app/addons/apps.py` → `index_classes`

**Remember**: Every new addon MUST be added to the `index_classes` list in `apps.py`!

---

_This guide provides a complete, production-ready implementation for monthly Elasticsearch index rotation in Django addons. Follow these steps exactly for reliable, scalable data management._
