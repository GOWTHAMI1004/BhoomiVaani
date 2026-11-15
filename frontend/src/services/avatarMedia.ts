export type ObjectUrlApi = Pick<typeof URL, 'createObjectURL' | 'revokeObjectURL'>;

export function createManagedObjectUrl(blob: Blob, urlApi: ObjectUrlApi = URL) {
  const url = urlApi.createObjectURL(blob);
  let revoked = false;
  return {
    url,
    revoke() {
      if (revoked) return;
      revoked = true;
      urlApi.revokeObjectURL(url);
    },
  };
}

export function getAvatarPlaybackMode(hasGeneratedVideo: boolean, hasGeneratedAudio: boolean): 'video' | 'audio' | 'unavailable' {
  if (hasGeneratedVideo) return 'video';
  if (hasGeneratedAudio) return 'audio';
  return 'unavailable';
}
