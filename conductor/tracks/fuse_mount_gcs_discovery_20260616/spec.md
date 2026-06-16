# Specification - Fuse-mount discovery folder on GCS (Track: fuse_mount_gcs_discovery_20260616)

## 1. Overview
Fuse-mount discovery folder on GCS

Issue URL: https://github.com/palladius/adk-sre-benjamin/issues/11

## 2. Description
I think we could START dipping our toes into file-sync on GCS since Cloud Run supports FUSe mount of GCS and gvien the low frequency of changes it seems like the right thing to do.

1. Copy some files/fodlers from local to GCS
2. configure GCS bucket / GCS PROJECT in .env. We cna use a default-over-configuration and JUST expect a project and do a gs://(PROJECT_ID)-sre-benjamin-discovery.
3. Create if it doesnt exist. Copy files across
4. Have some UI thing like 'syncing from GCs...'
5. Use local file system for files. Now i dont know if this is feasible, lets try it on linux/mac/. if not, lets figure it out with some `gsutil rsync` 

## hard part

* make fuse GCS work in localhost
* bydirectional sync if it doesnt work well is a pain
* ability to delete folders and shit -> these things ntend to become ADDITIVE and not SUBTRACTIVE. we need to be able to subrtact too!
* Think of folders RIGHT, one missing subfolder and we're done. Maybe gs://bucket/ENV/PROJ/<folders> like gs://BUCKET/prod/sre-investigations-demo/discovery/...


## 3. Acceptance Criteria
* The feature is fully implemented according to the issue requirements.
* Unit/integration tests are written and passing.
