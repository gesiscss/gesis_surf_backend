"""
Serializers for the mobile events API.
"""

from rest_framework import serializers

MODULES = ["accessibility", "vpn"]
MAX_EVENTS = 500


class ClientSerializer(serializers.Serializer):  # pylint: disable=abstract-method
    """
    Serializer for what the app reports about itself and its policy.
    """

    app_version = serializers.CharField(required=False, max_length=32)
    policy_version = serializers.CharField(required=False, max_length=32)
    policy_hash = serializers.CharField(required=False, max_length=71)
    policy_source = serializers.CharField(required=False, max_length=16)


class EventBatchSerializer(serializers.Serializer):  # pylint: disable=abstract-method
    """
    Serializer for an upload: events of one module, each sent as an object or
    as the raw JSON line. The events are checked one by one when they are stored.
    """

    module = serializers.ChoiceField(choices=MODULES)
    client = ClientSerializer(required=False)
    events = serializers.ListField(min_length=1, max_length=MAX_EVENTS)


class EventErrorSerializer(serializers.Serializer):  # pylint: disable=abstract-method
    """
    Serializer for an event that was not stored.
    """

    index = serializers.IntegerField(help_text="Position of the event in the request.")
    detail = serializers.CharField()


class EventResultSerializer(serializers.Serializer):  # pylint: disable=abstract-method
    """
    Serializer for the result of an upload: accepted + duplicates + rejected
    is always the number of events sent.
    """

    accepted = serializers.IntegerField()
    duplicates = serializers.IntegerField()
    rejected = serializers.IntegerField()
    errors = EventErrorSerializer(many=True)  # type: ignore[assignment]
