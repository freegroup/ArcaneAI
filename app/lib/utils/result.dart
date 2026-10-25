/// A success/failure value, as in the Flutter architecture guide. Lets the
/// data layer report failure without throwing across layers.
sealed class Result<T> {
  const Result();

  /// A successful result holding [value].
  const factory Result.ok(T value) = Ok<T>;

  /// A failed result holding [error].
  const factory Result.error(Object error) = Error<T>;
}

/// A successful [Result].
final class Ok<T> extends Result<T> {
  const Ok(this.value);

  /// The value.
  final T value;
}

/// A failed [Result].
final class Error<T> extends Result<T> {
  const Error(this.error);

  /// The error.
  final Object error;
}
