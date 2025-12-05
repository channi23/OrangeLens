# Protocol Version 0

This is the Initial version plannig of the protocol(for understanding and wirting the tasks that needs to be done)
## Overview
Basically we need to create a protocol that can be used to fiter the truth out of the posts and for that we have the decentralized infrastructrue, which for now we have only three nodes of them

Here we go

## VerificationRequest
Here we need one of the node where it can find out the 
* Content_type(text/image/video)
* text(optional)
* media_url(optional)
* source_url(optional)
* client_id/platform_id

Basically when the user wants to upload something on the internet, before uploading it, it will send a request to the node and the node will verify it and return the result to the user

## VerificationResult
Here one of the other node send the result as the tag

The Response includes:

* truth_score(0-100)
* confidence(low/medium/high)
* verdict(true/false/misleading/unknown/ more...)
* claims(list of citations)
* evidence(links,snippets,images)
* explanation(LLM text)
* manipulation_techniques

## Pramana Logs
This is going to be Hash based logs of the verification process

Where we store:

* content_type
* content_hash
* image_bytes
* source_url


## Pramāṇa-2PCV (Two-Phase Content Verification) - 
is a hash-based, privacy-preserving verification algorithm with two phases:
	1.	PREPARE phase – clients send a low-cost “hint” about upcoming content (type, size, early hash). Nodes use this to pre-warm models and resources, and optionally preload existing verdicts.
	2.	VERIFY phase – clients send the full content plus its content_hash. Nodes deduplicate work by first checking for existing verdicts keyed by content_hash, and only run heavy verification if none exist. Nodes never store raw content long term; they store only content hashes and minimal verdict metadata.

This design minimizes latency and redundant verification while aligning with a decentralized, privacy-conscious protocol ideology.








