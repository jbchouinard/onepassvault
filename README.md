# onepassvault
A tool for synchronizing secrets between 1Password and HashiCorp Vault KV store.

## Installation

It is recommended to use 1Password CLI Desktop app integration: https://developer.1password.com/docs/cli/get-started/

## Configuration

## Usage

## Security

This was developed for my personal use for homelab projects. I've attempted to make the tool 
fairly secure, e.g. secrets are never saved to disk or environment variables, but I make
no guarantees.

The tool supports some unsafe practices like keeping multiple Vault unseal keys in the
same place.
