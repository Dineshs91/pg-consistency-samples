"""
Here we will try to test optimistic locking with and without taking a row level lock.
"""
import time
import signal
import random
from multiprocessing import Process, Queue

import click
import psycopg2

dsn = "dbname=consistent user=postgres"
kill = False


def without_lock(q):
    """
    Here we try to simulate optimistic locking:
    1. User has a version no.
    2. He updates the content of the post.
    3. Another user also has the same version no.
    4. He also updates the content of the post.

    Race condition happens when a lock is not being used, as the value may change
    within the read and update query are executed.

    This example doesn't make the state inconsistent. This is just to show how things
    change between read and update queries.
    """
    with psycopg2.connect(dsn) as conn:
        kill = q.get()
        while not kill:
            with conn.cursor() as cur:
                random_text = str(random.random())
                cur.execute("SELECT version FROM post LIMIT 1;")
                version = cur.fetchone()[0]

                try:
                    cur.execute("UPDATE post SET content=%s, version=%s where VERSION=%s RETURNING version;",
                                (random_text, int(version) + 1, version))
                    conn.commit()

                    value = cur.fetchone()

                    if not value:
                        print("Failed old_value[{}], new_value[{}]".format(value, random_text))
                        q.put(True)
                        break

                except psycopg2.Error as e:
                    print(e)

                time.sleep(0.2)

                if not q.empty():
                    kill = q.get()


def with_lock(q):
    """
    Using FOR UPDATE lock from postgres.

    This is a row level lock.
    """
    with psycopg2.connect(dsn) as conn:
        kill = q.get()
        while not kill:
            with conn.cursor() as cur:

                random_text = str(random.random())
                cur.execute("SELECT version FROM post LIMIT 1 FOR UPDATE;")
                version = cur.fetchone()[0]

                try:
                    cur.execute("UPDATE post SET content=%s, version=%s where VERSION=%s RETURNING version;",
                                (random_text, int(version) + 1, version))
                    conn.commit()

                    value = cur.fetchone()

                    if not value:
                        print("Failed old_value[{}], new_value[{}]".format(value, random_text))
                        break

                except psycopg2.Error as e:
                    print(e)

                time.sleep(0.3)
                kill = q.get()


def handle_sigint(signal, frame):
    global kill

    print("\n Received sigint. Exiting...")
    kill = True


@click.command()
@click.option("--test", help="Specify which test to run")
def start(test):
    if not test:
        print("Please provide a value for --test option")
        exit(1)

    if test == "with_lock":
        target = with_lock
    elif test == "without_lock":
        target = without_lock
    else:
        print("Bad argument value for test")
        exit(1)

    signal.signal(signal.SIGINT, handle_sigint)
    print(target.__name__)
    q = Queue()

    processes = []
    no_of_processes = 2
    for _ in range(no_of_processes):
        process = Process(target=target, args=(q,))
        processes.append(process)
        process.start()
        q.put(False)

        time.sleep(1)

    while True:
        if kill:
            for _ in range(no_of_processes):
                q.put(True)
            break

        dead = True
        for p in processes:
            if p.is_alive():
                dead = False

        if dead:
            break

    q.close()
    q.join_thread()
    for process in processes:
        process.join()


if __name__ == "__main__":
    start()
