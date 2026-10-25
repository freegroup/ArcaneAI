/// Content delivery for ArcaneAI game packs.
///
/// Every file is addressed by a [ContentRef] and located by a
/// [ContentResolver] that asks its sources in order — typically
/// [BundledContentSource] (shipped with the app), [CacheContentSource]
/// (downloaded earlier) and [HttpContentSource] (downloaded on demand,
/// checksum-verified). Consumers only see [ResolvedContent]: an asset key or
/// a file path.
library;

export 'content.dart';
export 'content_resolver.dart';
export 'game_pack_loader.dart';
export 'pack_manifest.dart';
export 'sources.dart';
