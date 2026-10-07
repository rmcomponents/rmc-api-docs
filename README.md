# RMC Catalog API
#mit# OpenAPI 3.0 specification
The specification can be found [here](openapi-v3.yaml).

## Development status
- Error codes are not yet finalized.
- The response format for authentication messages will change in the future. Please rely
  only on the HTTP status codes for now.


## Authentication flow
The API uses the OAuth 2.0 _client credentials_ flow. Client credentials (`client_id` and `client_secret`) are exchanged for a limited-lifetime `access_token` through an authentication server. The access token must then be included with 
all API requests in the `Authorization` header:
```http
Authorization: <access_token>
```
Your application should keep track of the token lifetime and request a fresh access token from the authentication server
before the current token expires.

The production endpoints are:
- Authentication server (`auth_base_url`): `https://rmcapi.auth.eu-central-1.amazoncognito.com`
- API base URL (`api_base_url`): `https://stq74hnyoh.execute-api.eu-central-1.amazonaws.com/production`



### Python example
See [auth_flow.example.py](auth_flow.example.py) for an example implementation.


## Example requests
#### Request access token (cURL)
```bash
curl -X POST "https://rmcapi.auth.eu-central-1.amazoncognito.com/oauth2/token" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "grant_type=client_credentials" \
     -d "scope=rmcapi/read" \
     --data-urlencode "client_id=<client_id>" \
     --data-urlencode "client_secret=<client_secret>"
```
#### Request single part number
```http
POST /production/v1/catalog/query HTTP/1.1
Host: stq74hnyoh.execute-api.eu-central-1.amazonaws.com
Content-Type: application/json
Authorization: <access_token>

{
  "part_number": [ "UMK123ABC-Z" ],
  "test_mode": true
}
```

#### Batch request multiple part numbers
```http
POST /production/v1/catalog/query HTTP/1.1
Host: stq74hnyoh.execute-api.eu-central-1.amazonaws.com
Content-Type: application/json
Authorization: <access_token>

{
  "part_number": [ "UMK123ABC-Z", "UMK123ABC", "UMK456DEFZ" ],
  "test_mode": true
}
```

#### Multiple part numbers, ignoring empty values
Requesting empty part numbers will return an error by default. Setting `ignore_empty_parts` to `true` allows you to ignore empty values for easier mapping between the input array indices and the corresponding output records.
```http
POST /production/v1/catalog/query HTTP/1.1
Host: stq74hnyoh.execute-api.eu-central-1.amazonaws.com
Content-Type: application/json
Authorization: <access_token>

{
  "part_number": [ "UMK123ABC-Z", "UMK123ABC", " ", "UMK456DEFZ" ],
  "ignore_empty_parts": true,
  "test_mode": true
}
```

## Testing

For testing purposes, the following part numbers will return valid (but fictious) data if `test_mode` is set to `true` in the request body:

```
UMK123ABC
UMK123ABC-Z
UMK456DEF
UMK456DEF-Z
PN-0001
PN-0002
...
PN-1000
```

## Versioning
The API uses semantic versioning:
- Minor versions will be fully backwards-compatible (starting with `1.0.0`).
- Major versions will be released under separate endpoints.


## Limits

The following limits apply:

| Description | Limit      | Unit                |
|--------------|------------|---------------------|
| Request rate (sustained / burst) | 5.000  | requests/s  |
| Access token requests (per IP) | 30 | requests / 5 min |
| Batch query  | 500        | part numbers        |

Exceeding the access token request limit returns HTTP 403. To avoid hitting these
limits, implement exponential backoff when requesting access tokens and making API
requests, and retry after a short delay on `403`/`429` responses.




## Notes
- Note that minor version bumps can introduce new fields to the API schema. Please
  make sure your application handles such changes gracefully. Any unknown fields 
  should be ignored.
- Please don't create issues on GitHub.
