/**
 * Type-level shim over @hey-api/client-fetch.
 *
 * The published client (0.13.1) honours per-request `headers`,
 * `bodySerializer` and a `client` override at runtime, but its type
 * definitions (a) do not surface those options on `Options`, (b) require
 * `url` on TDataShape while generated `*Data` types carry it only at the
 * call site, and (c) collapse `data` to `TData[keyof TData]`, losing the
 * response structure entirely. This module re-exports the runtime with the
 * corrected types in one place; `scripts/patch-client.mjs` repoints the
 * generated imports here after every generation. Delete this file when the
 * published types catch up.
 */
import {
  buildClientParams,
  createClient as createClientImpl,
  createConfig,
  formDataBodySerializer,
  jsonBodySerializer,
  urlSearchParamsBodySerializer,
} from "@hey-api/client-fetch";
import type {
  Auth,
  Config as BaseConfig,
  CreateClientConfig,
  QuerySerializerOptions,
  RequestOptions,
  ResponseStyle,
  TDataShape,
} from "@hey-api/client-fetch";

export {
  createConfig,
  urlSearchParamsBodySerializer,
  formDataBodySerializer,
  jsonBodySerializer,
  buildClientParams,
};

export type {
  Auth,
  CreateClientConfig,
  QuerySerializerOptions,
  RequestOptions,
  ResponseStyle,
  TDataShape,
};

export interface Config extends BaseConfig {}

export type Options<
  TData extends TDataShape = TDataShape,
  ThrowOnError extends boolean = boolean,
> = Omit<RequestOptions, "url"> &
  Omit<TData, "url" | "body"> & {
    client?: Client;
    // Body is pre-serialized by callers that need a non-JSON encoding
    // (e.g. the OAuth2 password form), so any BodyInit is allowed here.
    body?: unknown;
  };

export type RequestResult<
  TData = unknown,
  TError = unknown,
  ThrowOnError extends boolean = false,
> = ThrowOnError extends true
  ? Promise<TData>
  : Promise<
      (
        { data: TData; error: undefined } | { data: undefined; error: TError }
      ) & {
        request: Request;
        response: Response;
      }
    >;

type MethodFn = <
  TData = unknown,
  TError = unknown,
  ThrowOnError extends boolean = false,
>(
  options: Options<TDataShape, ThrowOnError> & { url: string },
) => RequestResult<TData, TError, ThrowOnError>;

export interface Client {
  buildUrl: <TData extends { url: string }>(
    options: Pick<TData, "url"> & Options<TData>,
  ) => string;
  connect: MethodFn;
  delete: MethodFn;
  get: MethodFn;
  getConfig: () => Config;
  head: MethodFn;
  interceptors: {
    request: {
      use: (fn: (req: Request) => Request | Promise<Request>) => number;
    };
  };
  options: MethodFn;
  patch: MethodFn;
  post: MethodFn;
  put: MethodFn;
  request: MethodFn;
  setConfig: (config: Partial<Config>) => Config;
  trace: MethodFn;
}

export function createClient(config: Partial<Config> = {}): Client {
  return createClientImpl(config) as unknown as Client;
}
