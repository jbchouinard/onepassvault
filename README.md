# onepassvault

A tool for synchronizing secrets between 1Password and HashiCorp Vault KV store.

## Features
- Store and retrieve Vault credentials from 1Password
- Push or pull secrets between 1Password and Vault KV store

## Requirements

- 1Password CLI: op version 2.25.0+

Sign-in with 1Password CLI Desktop app integration: https://developer.1password.com/docs/cli/get-started/

## Security

This tool was developed for my personal use and experimentation. I've tried to make the tool 
as secure as possible, e.g. secrets are never saved to disk or environment variables, but it is
not battle-tested.

## Installation

With pipx:
```sh
pipx install git+https://github.com/jbchouinard/onepassvault.git
```

## Configuration

### opvault

### 1Password

### Vault

## Usage

## Development

### Tests

This repo contains integration test that use a live 1Password account. All tests are done on
a newly created vault, but it is not recommended to run with the tests on an account with anything important.

To run the tests, set the OPV_TEST_ACCOUNT_URL (e.g. my.1password.com) and
OPV_TEST_ACCOUNT_EMAIL environment variables to a test account and run:

```sh
poetry run pytest tests
```
