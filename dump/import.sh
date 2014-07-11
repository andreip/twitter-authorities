#!/bin/bash

# Run as
# ./dump/import.sh from root folder.
mongorestore dump/licenta/halep.bson
mongorestore dump/licenta/halep_features.bson
mongorestore dump/licenta/halep_metrics.bson
mongorestore dump/licenta/ukraine\ gas\ russia.bson
mongorestore dump/licenta/ukraine\ gas\ russia_features.bson
mongorestore dump/licenta/ukraine\ gas\ russia_metrics.bson
