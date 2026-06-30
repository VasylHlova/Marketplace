import pytest
from botocore.exceptions import BotoCoreError

from app.tasks.media_processor import process_media_task


@pytest.mark.unit
def test_process_media_task_success(mocker, faker):
    mock_run = mocker.patch("app.tasks.media_processor._run")
    mock_asyncio_run = mocker.patch("app.tasks.media_processor.asyncio.run")

    entity_id = faker.uuid4()
    entity_type = "product"
    path = f"products/{entity_id}/test.png"

    process_media_task(entity_id=entity_id, entity_type=entity_type, original_media_path=path)

    mock_run.assert_called_once_with(str(entity_id), str(entity_type), path)
    mock_asyncio_run.assert_called_once()


@pytest.mark.unit
def test_process_media_task_retry(mocker, faker):
    _mock_run = mocker.patch("app.tasks.media_processor._run")  # noqa: F841
    mock_asyncio_run = mocker.patch("app.tasks.media_processor.asyncio.run")

    mock_asyncio_run.side_effect = BotoCoreError()

    mock_retry = mocker.patch("celery.app.task.Task.retry")
    mock_retry.side_effect = Exception("Retry triggered")

    entity_id = faker.uuid4()
    entity_type = "product"
    path = f"products/{entity_id}/test.png"

    with pytest.raises(Exception, match="Retry triggered"):
        process_media_task(entity_id=entity_id, entity_type=entity_type, original_media_path=path)

    mock_retry.assert_called_once()
    assert isinstance(mock_retry.call_args.kwargs["exc"], BotoCoreError)


@pytest.mark.asyncio
@pytest.mark.unit
async def test_run_internal(mocker, faker):
    from app.tasks.media_processor import _run

    mock_storage = mocker.patch("app.tasks.media_processor.MinioStorageClient")
    mock_session_maker = mocker.patch("app.tasks.media_processor.async_session")
    mock_session = mocker.AsyncMock()
    mock_session_maker.return_value.__aenter__.return_value = mock_session
    mock_repo = mocker.patch("app.tasks.media_processor.SqlMediaRepository")
    mock_process_media = mocker.patch(
        "app.tasks.media_processor.process_media", new_callable=mocker.AsyncMock
    )

    entity_id = faker.uuid4()
    entity_type = "product"
    path = f"products/{entity_id}/test.png"

    await _run(entity_id, entity_type, path)

    mock_storage.assert_called_once()
    mock_repo.assert_called_once_with(mock_session)
    mock_process_media.assert_called_once_with(
        entity_id, entity_type, path, mock_storage.return_value, mock_repo.return_value
    )
