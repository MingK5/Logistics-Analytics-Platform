@echo off
call .venv\Scripts\activate
python -m backend.app.producers.replay_producer --delay 2 --batch-size 10
