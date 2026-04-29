#! /usr/bin/env ruby

require 'securerandom'

external_id = SecureRandom.alphanumeric(20)

puts external_id
