/**
 * @author Tom
 */

type("DataReference", ["Source", "WatchGetter"], {
	id: Getter,
	revision: Getter
});

type("DataStore", ["DataReference"], {
	getReference: function(id, revision) {},
	fetchNew: function(handler) {},
	submit: function(id, data) {}
},
	function(url) {
		var store = this;
		var latestReferences = {};
		var latestReferencesUpdate = {};
		var toSubmit = {};
		var toGetLatest = {};
		var newIdHandlers = [];
		var newIds = [];
		var newIdsWanted = 0;
		
		function commit() {
			var body;
			if (!empty(toGetLatest)) {
				body.getLatestRevisions = enumerate(toGetLatest, stacker(function(value, key) {
					return key;
				}));
				toGetLatest = {};
			}
			if (!empty(toSubmit)) {
				body.submit = toSubmit;
				toSubmit = {};
			}
			var newIdsNeeded = newIdsWanted - newIds.length + 10;
			if (newIdsNeeded > 0) {
				newIdsWanted = 0;
				body.getNewIds = newIdsNeeded + 10;
			}
			if (empty(body)) {
				return;
			}
			body.date = new Date().toString();
			jsonRequest(url, body, function(result, error) {
				if (exists(result) && !exists(error)) {
					enumerate(result.latestRevisions, function(value, key) {
						var update = latestReferencesUpdate[key];
						if (exists(update)) {
							update(value);
						}
					});
					newIds.splice(newIds.length, 0, result.newIds);
					iterate(newIdHandlers, function(handler) {
						thisStore.fetchNew(handler);
					});
					enumerate(result.submitErrors, function(value, key) {
						// TODO
					});
				} else {
					// TODO
				}
			});
		}
		function getLatest(id) {
			toGetLatest[id] = true;
			schedule(commit);
		}
		
		/**
		 * 
		 * @param {String} id
		 * @param {String, Function} revision | initializer
		 */
		store.getReference = function(id, revision) {
	  	var reference;
			if (!exists(revision)) {
				reference = latestReferences[id];
				if (exists(reference)) {
					return reference;
				}
			}
			reference = new DataReference();
			var object = mixWatchGetters(self, ["state", "error"]);
			mixinInstance(reference, object.accessor("data"), WatchGetter);
			var observeData = reference.observe;
			var observersCount = 0;
			
	  	function update(rev) {
	  		if (exists(rev)) {
	 				webGet(url + id + "/" + rev, function(result, error) {
		  			if (exists(error)) {
		  				object.update({
		  					state: SourceState.Error,
		  					error: error
		  				});
		  			} else {
		  				object.update({
		  					state: SourceState.Loaded,
		  					error: null,
		  					data: Json.read(result)
		  				});
		  			}
		  		});
				} else {
					if (isFunction(revision)) {
				  	submit(id, revision());
				  } else {
				  	object.update({
				  		state: SourceState.Loaded,
				  		error: null,
				  		data: null
				  	});
				  }
				}
	  	}
			if (!exists(revision)) {
				latestReferences[id] = reference;
				latestReferencesUpdate[id] = update;
			}
			
			reference.id = new Getter(function() {
				return id;
			});
			reference.revision = new Getter(function() {
				return revision;
			});
	  	reference.refresh = function() {
	  		object.update({
	  			state: SourceState.Loading,
	  			error: null
	  		});
	  		if (exists(revision)) {
	  			update(revision);
	  		} else {
	  			getLatest(id);
	  		}
	  	};
			reference.observe = function(observer) {
				if (observersCount++ == 0) {
					reference.refresh();
				}
				var stop = observeData(observer);
				return function() {
					if (!stop()) {
						return false;
					}
					if (--observersCount == 0) {
						object.set("data", null);
					}
					return true;
				};
			};
	  	object.update({
	  		state: SourceState.None,
	  		error: null,
				id: id,
				revision: revision,
	  		data: null
	  	});
			return reference;
	  };
		store.fetchNew = function(handler) {
			var count = getArgumentsCount(handler);
			if (newIds.length >= count) {
				handler.apply(null, newIds.splice(0, count));
			} else {
				newIdHandlers.push(handler);
				newIdsWanted += count;
			}
			schedule(commit);
		};
		store.submit = function(id, data) {
			toSubmit[id] = data;
			schedule(commit);
		};
	}
);
