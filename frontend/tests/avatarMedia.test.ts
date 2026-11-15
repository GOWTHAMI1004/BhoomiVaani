import test from 'node:test';
import assert from 'node:assert/strict';
import { createManagedObjectUrl, getAvatarPlaybackMode } from '../src/services/avatarMedia.ts';

test('revokes a generated video object URL once on cleanup', () => {
  const revoked: string[] = [];
  const managed = createManagedObjectUrl(new Blob(['mp4']), {
    createObjectURL: () => 'blob:generated-avatar',
    revokeObjectURL: (url) => revoked.push(url),
  });
  assert.equal(managed.url, 'blob:generated-avatar');
  managed.revoke();
  managed.revoke();
  assert.deepEqual(revoked, ['blob:generated-avatar']);
});

test('uses returned video when available and retains Timbre audio fallback', () => {
  assert.equal(getAvatarPlaybackMode(true, true), 'video');
  assert.equal(getAvatarPlaybackMode(false, true), 'audio');
  assert.equal(getAvatarPlaybackMode(false, false), 'unavailable');
});
