from __future__ import annotations

import discord
import pytest

from discord.components import UnfurledMediaItem
from discord.http import HTTPClient


@pytest.mark.parametrize(
    ('flag_name', 'bit'),
    [
        ('contains_explicit_content', 1 << 4),
        ('contains_gore_content', 1 << 6),
        ('contains_self_harm_content', 1 << 7),
    ],
)
def test_attachment_flags(flag_name, bit):
    flags = discord.AttachmentFlags._from_value(bit)
    assert getattr(flags, flag_name)


@pytest.mark.parametrize(
    ('flag_name', 'bit'),
    [
        ('contains_explicit_content', 1 << 4),
        ('contains_gore_content', 1 << 6),
        ('contains_self_harm_content', 1 << 7),
    ],
)
def test_embed_flags(flag_name, bit):
    embed = discord.Embed.from_dict({'flags': bit})
    assert getattr(embed.flags, flag_name)


def test_explicit_media_flag_alias_is_preserved():
    flags = discord.AttachmentFlags(contains_explicit_media=True)
    assert flags.contains_explicit_content
    assert flags.value == 1 << 4


def test_unfurled_media_item_content_scan_metadata():
    item = UnfurledMediaItem._from_data(
        {
            'url': 'https://cdn.discordapp.com/attachments/1/2/image.png',
            'content_scan_metadata': {'flags': 0b110, 'version': 3},
        },
        None,
    )
    assert item.content_scan_metadata.flags.gore
    assert item.content_scan_metadata.flags.self_harm
    assert item.content_scan_metadata.version == 3


@pytest.mark.asyncio
async def test_create_invite_includes_target_user_ids(monkeypatch):
    calls = []

    async def request(self, route, **kwargs):
        calls.append((route, kwargs))
        return {}

    monkeypatch.setattr(HTTPClient, 'request', request)
    client = object.__new__(HTTPClient)
    await HTTPClient.create_invite(client, 123, target_user_ids=[456, 789])
    route, kwargs = calls[0]
    assert route.method == 'POST'
    assert route.url.endswith('/channels/123/invites')
    assert kwargs['json']['target_user_ids'] == [456, 789]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ('method_name', 'http_method', 'path', 'payload'),
    [
        ('add_invite_target_user', 'PUT', '/invites/code/target-users/456', None),
        ('remove_invite_target_user', 'DELETE', '/invites/code/target-users/456', None),
        ('bulk_add_invite_target_users', 'POST', '/invites/code/target-users/bulk-add', {'user_ids': [456, 789]}),
        ('bulk_delete_invite_target_users', 'POST', '/invites/code/target-users/bulk-delete', {'user_ids': [456, 789]}),
    ],
)
async def test_invite_target_user_routes(monkeypatch, method_name, http_method, path, payload):
    calls = []

    async def request(self, route, **kwargs):
        calls.append((route, kwargs))
        return None

    monkeypatch.setattr(HTTPClient, 'request', request)
    client = object.__new__(HTTPClient)
    method = getattr(HTTPClient, method_name)
    if method_name.endswith('_user'):
        await method(client, 'code', 456)
    else:
        await method(client, 'code', [456, 789])
    route, kwargs = calls[0]
    assert route.method == http_method
    assert route.url.endswith(path)
    if payload is not None:
        assert kwargs['json'] == payload
