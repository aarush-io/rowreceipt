// Independent Node implementation for the v1 interoperability vector only.
import { createHash, createHmac } from 'node:crypto';

const sha256 = message => createHash('sha256').update(message).digest();
const hmac = (key, message) => createHmac('sha256', key).update(message).digest();

function sortKeys(value) {
  if (Array.isArray(value)) return value.map(sortKeys);
  if (value && typeof value === 'object') {
    return Object.fromEntries(Object.keys(value).sort().map(key => [key, sortKeys(value[key])]));
  }
  return value;
}

function json(value) {
  return JSON.stringify(sortKeys(value));
}

function integer(value) {
  const bytes = Buffer.alloc(9);
  bytes[0] = 'I'.charCodeAt(0);
  bytes.writeBigInt64BE(BigInt(value), 1);
  return bytes;
}

function text(value) {
  if (value === null) return Buffer.from('N');
  const bytes = Buffer.from(value);
  const tag = Buffer.alloc(5);
  tag[0] = 'T'.charCodeAt(0);
  tag.writeUInt32BE(bytes.length, 1);
  return Buffer.concat([tag, bytes]);
}

const key = Buffer.from(Array.from({ length: 32 }, (_, index) => index));
const input = [[1, 'east', null], [-2, 'west', 'café']];
const contract = {
  format: 'rowreceipt-contract/1',
  dataset: 'portable-fixture',
  fields: [
    { name: 'id', type: 'integer', nullable: false },
    { name: 'region', type: 'text', nullable: false },
    { name: 'name', type: 'text', nullable: true },
  ],
  key: ['id', 'region'],
  buckets: 16,
};
const digest = sha256(json(contract));
const derive = purpose => hmac(key, Buffer.concat([Buffer.from('rowreceipt/1\0' + purpose + '\0'), digest]));
const partitions = Array.from({ length: contract.buckets }, () => []);

for (const [id, region, name] of input) {
  const identity = Buffer.concat([integer(id), text(region)]);
  const token = hmac(derive('key'), identity);
  const partition = token.readUInt16BE(0) & (contract.buckets - 1);
  partitions[partition].push([token, hmac(derive('row'), Buffer.concat([identity, text(name)]))]);
}

const payload = {
  format: 'rowreceipt/1',
  contract: digest.toString('hex'),
  key_id: derive('id').toString('hex'),
  buckets: partitions.map((rows, index) => {
    const number = Buffer.alloc(2);
    number.writeUInt16BE(index);
    rows.sort(([left], [right]) => Buffer.compare(left, right));
    return [rows.length, hmac(derive('bucket'), Buffer.concat([number, ...rows.flat()])).toString('hex')];
  }),
};
const signed = { ...payload, mac: hmac(derive('receipt'), json(payload)).toString('hex') };
console.log(JSON.stringify({
  contract,
  key_hex: key.toString('hex'),
  input,
  contract_sha256: digest.toString('hex'),
  receipt_mac: signed.mac,
  receipt_sha256: sha256(json(signed) + '\n').toString('hex'),
}, null, 2));
