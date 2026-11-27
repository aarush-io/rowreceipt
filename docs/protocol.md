# RowReceipt v1 interchange format

An exchange uses a shared contract, a fresh 32-byte comparison key, and two receipts. The key travels separately through an approved secure channel. Agree independently on which versions or time ranges each side is capturing.

## Contract

A JSON object has exactly these fields.

| Field | Definition |
|---|---|
| `format` | Literal `rowreceipt-contract/1`. |
| `dataset` | Logical identifier for this comparison. Use a purpose-specific identifier. |
| `fields` | Ordered array of 1 to 128 definitions with `name`, `type` and optional Boolean `nullable` defaulting to false. |
| `key` | Ordered, nonempty array of distinct field names. Key fields must be non-nullable. |
| `buckets` | A power of two from 16 through 4096. Use 64 for the default-sized exchange. |

Identifiers match ASCII `[A-Za-z_][A-Za-z0-9_.-]{0,63}`. Field names are unique. Allowed types are `integer`, `real`, `text` and `bytes`. Physical names are capture-local and stay outside the contract. An optional mapping JSON object maps logical names to exact physical names, with identity used for omitted fields. All selected physical names must be distinct.

Normalize the contract by including each `nullable` field. The contract digest is SHA-256 of its canonical JSON bytes. In this format canonical JSON uses ASCII, lexicographically sorted object keys, no spaces outside strings, base-10 integers, lowercase Boolean values and unchanged array order. The accepted interchange documents contain only ASCII strings in protocol fields. Reject duplicate object keys and unknown fields.

## Canonical values

| Value | Byte encoding |
|---|---|
| Null | ASCII `N`. Only allowed for a nullable field. |
| Integer | ASCII `I` then a signed 64-bit two's-complement integer in big-endian byte order. |
| Real | ASCII `R` then a finite IEEE 754 binary64 in big-endian byte order. Both signed zeros encode as positive zero. An integer presented as a real must be exactly representable if it arrived from a typed adapter. CSV decimal tokens define binary64 rounded from decimal. |
| Text | ASCII `T`, then a big-endian unsigned 32-bit length and UTF-8 bytes. Equality uses exact code points, including case and whitespace. |
| Bytes | ASCII `B`, then a big-endian unsigned 32-bit length and raw bytes. |

Construct the key message by concatenating encodings in key order. Construct the row message by concatenating encodings in field order. Invalid values, malformed records, null keys or repeated keys fail the entire capture. The CLI accepts at most 8 MiB of encoded data per row and 64 KiB per contract or mapping.

CSV uses comma delimiters, double-quote escaping, UTF-8 with an optional BOM and a required header. Unmapped columns are ignored after structural validation. The exact token `\N` denotes null, including inside a quoted cell. To represent text beginning with a backslash, double its first backslash. Empty text and empty bytes are valid values. CSV integers accept 1 to 19 decimal digits and an optional sign. The number must fit in signed 64 bits. Real fields accept signed decimal and exponent notation and reject infinities and NaNs. Bytes use an even number of hexadecimal digits. The CLI enforces a record budget of 2 Mi characters including line breaks and 128 Ki characters per field. The standard library parser's configured field limit can further constrain embedded callers.

## Receipt construction

Let `MAC(k, x)` be HMAC-SHA-256 returning 32 bytes. Let `D` be the raw 32-byte contract digest. Derive context-specific secrets using the master key `K`.

```text
subkey(purpose) = MAC(K, ASCII("rowreceipt/1") || 00 || ASCII(purpose) || 00 || D)
fingerprint     = MAC(subkey("key"), key-message)
content         = MAC(subkey("row"), row-message)
bucket          = first two fingerprint bytes as uint16 big-endian AND (buckets - 1)
```

For each bucket, sort pairs by fingerprint bytes in ascending unsigned lexicographic order. The bucket commitment is `MAC(subkey("bucket"), bucket-number || fingerprint1 || content1 || …)`. A bucket number is a two-byte big-endian integer. An empty bucket commits to its number alone.

A receipt is a JSON object with the following fields.

| Field | Definition |
|---|---|
| `format` | Literal `rowreceipt/1`. |
| `contract` | Lowercase hex encoding of `D`. |
| `key_id` | Lowercase hex encoding of `subkey("id")`. |
| `buckets` | Array ordered by bucket number. Each entry is `[row-count, lowercase-hex-commitment]`. Counts and their sum are between zero and signed 64-bit maximum. |
| `mac` | Lowercase hex of `MAC(subkey("receipt"), canonical JSON of the object with mac removed)`. |

The reference writer emits the full object as canonical JSON followed by one LF. A reader accepts harmless JSON whitespace or object key reordering. The implementation caps receipts at 512 KiB. Authenticate the ID and MAC with the provided key before comparing. Compare only matching format, contract digest and bucket count. Report each bucket whose count or commitment differs.

Counts and bucket changes leak information about a dataset and may be sensitive. Holders of the shared key can manufacture valid receipts, run targeted guesses and replay old receipts. The design assumes trusted capture operators and an agreed snapshot cutoff. Public verifiability, source identity, capture freshness and disclosure resistance against the other key holder are outside v1. [HMAC standard](https://www.rfc-editor.org/rfc/rfc2104) · [Independent test vector](../tests/vector.json)

Regenerate the interoperability vector with `node tests/make_vector.mjs` from the checkout root.
