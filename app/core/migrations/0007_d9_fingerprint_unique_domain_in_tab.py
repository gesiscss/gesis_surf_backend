"""
D9: unique_domain_in_tab -> MD5 fingerprint index (B8).

The old index stored full (domain_title, domain_url) in a btree
index entry. Index entries are limited (2704 bytes on glibc PG16),
so long URLs raised 'index row size exceeds btree maximum' and the
whole request failed (data-loss investigation, 2026-11). The new
index stores MD5(title)/MD5(url) (32 hex chars each) so it can never
overflow. It also adds `user` to the key: the constraint now scopes
per participant (as the name always implied) instead of across users.

No columns change, no data rewrites. Rollback is one-way (once
long-URL rows exist the old exact-text index cannot be rebuilt), so
the reverse migration refuses to run rather than leave the table
without any duplicate rule.
"""

from django.db import migrations, models
from django.db.models import Func


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0006_selectorconfig_extension_selector_version_and_more"),
    ]

    operations = [
        # Drop the old exact-text constraint, add the fingerprint one.
        # Same name so Django's model state stays aligned; Remove+Add
        # is the Django-native way (there is no AlterUniqueConstraint).
        migrations.RemoveConstraint(
            model_name="domain",
            name="unique_domain_in_tab",
        ),
        migrations.AddConstraint(
            model_name="domain",
            constraint=models.UniqueConstraint(
                "user",
                Func("domain_title", function="MD5"),
                Func("domain_url", function="MD5"),
                "start_time",
                name="unique_domain_in_tab",
            ),
        ),
    ]