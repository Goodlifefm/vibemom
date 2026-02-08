import { useEffect, useState } from 'react';
import { getBuildStampCached, loadBuildStampFromBuildJson, type BuildStamp } from './buildStamp';

export function useBuildStamp(): BuildStamp {
  const [stamp, setStamp] = useState<BuildStamp>(() => getBuildStampCached());

  useEffect(() => {
    let alive = true;
    (async () => {
      const loaded = await loadBuildStampFromBuildJson();
      if (!alive || !loaded) {
        return;
      }
      setStamp(loaded);
    })();

    return () => {
      alive = false;
    };
  }, []);

  return stamp;
}

