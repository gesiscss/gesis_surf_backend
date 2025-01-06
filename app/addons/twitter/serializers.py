"""
Serializers for Twitter data.
"""

from rest_framework import serializers


class TwitterDataSerializer(serializers.Serializer):
    """
    Serializer for Twitter data.
    """

    tweet_id = serializers.CharField(max_length=100)
    username = serializers.CharField(max_length=100)
    content = serializers.CharField()
    timestamp = serializers.DateTimeField()

    def create(self, validated_data: dict) -> object:
        """
        Create a new TwitterData instance.
        """
        raise NotImplementedError("We handle creation in the View.")

    def update(self, instance: object, validated_data: dict) -> object:
        """
        Update an existing TwitterData instance.
        """
        raise NotImplementedError("We handle updating in the View.")
