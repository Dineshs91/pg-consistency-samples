### Optimistic locking
This type of locking can be useful when multiple users try to update the same resource.

The way it works is, every row has a version number and when an update is being done,
it is applied only if it has not changed. If it has changed, it means that it was updated
by another user. We can show a message to the user saying, "the data has been updated
by some other user, please refresh the page."

We have to make sure that read and update should happen as a single operation. Otherwise
there will be race conditions.

**Example:**
In django, we can do this

`Posts.objects.filter(id=10, version=12).update(content=content)`

### Row level lock (Pessimistic locking)
Say, you have to update the row, only if certain conditions are met and the conditions
are complex which cannot be expressed in a single sql query, then we need to take a lock
on the row. Once we have the lock, no other thread/process cannot modify the row on which
we have a lock on.

### Serializable isolation level
This is a feature of the database, which detects any race conditions and aborts automatically.
It's up to the client how it handles the abort. The transaction can be retried or just
abort displaying the message to the user.


## Usage

`python consistent.py --test with_update_lock`

Test argument can have the following options

- with_optimistic_lock
- with_update_lock
- with_serializable
