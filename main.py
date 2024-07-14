import asyncio
import aiohttp
import os

URL = os.environ.get('TARGET_URL', 'https://localhost:8080/')
FILENAME = "dicByAI.txt"

# Признаки того что это страница 404
badPatternWithBadStatus = ["error404"]

maxWorkers = 50  # Ограничение количества потоков в пуле
Timeout = 500


##### Здесь можешь помечать найденные файлы,папки как захочешь. У меня все сделано тупо: False - фигня полная. Всё остальное должно заинтересовать.
async def check_url(path, semaphore, session):
    async with semaphore:
        url = f"{URL}/{path}"
        status = None
        text = None
        try:
            async with session.get(url, timeout=Timeout) as response:
                status = response.status
                text = await response.text()
                is_badPatternContained = (badPatternWithBadStatus in text for text in badPatternWithBadStatus)
                is_SmallDocumment = len(text) < 2000
                is_OkStatus = status == 200

                if(is_badPatternContained and status == 404):
                    return path, False

                if(not is_OkStatus):
                    return path, True
                
                if(is_SmallDocumment):
                    return path, True

                return path, None
        except Exception as e:
            print(f"URL {url} failed with exception: {str(e)}")
            return path, type(e)

#####
async def display_progress(total, tasks, interval=1):
    while len(tasks) < total:
        print_progress(total, tasks)
        await asyncio.sleep(interval)

def print_progress(total, tasks):
    founded = sum(1 for item in tasks if isinstance(item, tuple) and len(item) > 1 and item[1] is True)
    checked = len(tasks)
    print(f"\rChecked: {checked}, Founded: {founded}, Progress: {(checked / total) * 100:.2f}%", end='')


#####
async def run_tasks(paths, maxWorkers):
    tasks = []
    semaphore = asyncio.Semaphore(maxWorkers)

    progress_task = asyncio.create_task(display_progress(len(paths), tasks))
    results = await asyncio.gather(*tasks)

    connector = aiohttp.TCPConnector(limit=250, limit_per_host=250)
    async with aiohttp.ClientSession(connector=connector) as session:
        for path in paths:
            task = await check_url(path, semaphore, session)
            tasks.append(task)

    _ = results
    _ = progress_task
    print_progress(len(paths), tasks)
    print("\n")
    return tasks

async def main():
    with open(FILENAME, 'r') as file:
        paths = [line.strip() for line in file if line.strip()]
    
    results = await run_tasks(paths, maxWorkers)


    tt = [item for item in results if isinstance(item, tuple) and len(item) > 1 and item[1] is not False]

    for el in tt:
        print(f"Status: {el[1]}; URL: {URL}/{el[0]}")


    print("")

if __name__ == "__main__":
    asyncio.run(main())