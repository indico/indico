/**
 * @author Tom
 */

/**
 * Returns an observable representation of the target.
 * @param {Object} target
 * @return {WatchList, WatchObject, Object}
 */
function watchize(target) {
	if (!exists(target) || !isObject(target)) {
		return target;
	}
	if (isArray(target)) {
		var list = new WatchList();
		iterate(target, function(item) {
			list.append(watchize(item, setter));
		});
		return list;
	}
	var object = new WatchObject();
	enumerate(target, function(target, key) {
		object.set(key, watchize(target));
		init(object, key, object.accessor(key)); 
	});
	return object;
}

/**
 * Observes the target and invokes the commit function if the target or its items has been changed.
 * Returns the target.
 * @param {Object} target
 * @param {Function} commit
 * @return {Object}
 */
function watch(target, commit) {
	if (isObject(target)) {
		if (target.WatchGetter) {
			target.observe(function(value, old) {
				if (exists(old)) {
					unwatch(old, commit);
				}
				if (exists(value)) {
					watch(value, commit);
				}
				commit();
			});
  	} else if (target.WatchList) {
			target.observe({
				itemAdded: function(item, index, self) {
					watch(item, commit);
					commit();
				},
				itemRemoved: function(item, index, self) {
					unwatch(item, commit);
					commit();
				}
			});
		} else if (target.WatchObject) {
			target.observe(function(value, key, self, old) {
				if (exists(old)) {
					unwatch(old, commit);
				}
				if (exists(value)) {
					watch(value, commit);
				}
				commit();
			});
		} else {
			each(target, function(value) {
				watch(value, commit);
			});
		}
	}
	return target;
}

function unwatch() {
	// TODO
}
