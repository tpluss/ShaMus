var dqs = function(selector) { return document.querySelector(selector); }

function getCookie(name, isDisposable) {
	var matches = document.cookie.match(new RegExp(
		"(?:^|; )" + name.replace(/([\.$?*|{}\(\)\[\]\\\/\+^])/g, '\\$1') + "=([^;]*)"
	));

	var cookieVal = matches ? decodeURIComponent(matches[1]) : undefined;

	if (isDisposable && cookieVal) {
		document.cookie = name + "=; Path=/; Domain=" + window.location.hostname + "; Max-Age=-1;";
	}

	return cookieVal;
}

var player = {
	init: function() {
		var pO = this;
		this.au = dqs("#shamus");
		if (!this.au) { return; }

		this.durationSlider = dqs("#player_track_duration_slider");
		this.durationTimer = dqs("#player_track_duration_timer");
		this.muteBtn = dqs("#player_volume_button");
		this.prevVolume = 0;
		this.volumeSlider = dqs("#player_volume_slider");
		this.playBtn = dqs("#player_btn_pl");
		this.pauseBtn = dqs("#player_btn_pa");
		this.nextBtn = dqs("#player_btn_ne");
		this.prevBtn = dqs("#player_btn_pr");
		this.repeatBtn = dqs("#player_btn_re");
		this.randomBtn = dqs("#player_btn_ra");
		this.radioBtn = dqs("#player_btn_rd");
		this.repeatMode = false;
		this.randomMode = false;
		this.radioMode = false;

		this.durationSlider.addEventListener("click", function(e) {
			if (!pO.au.duration) { return }
			var percent = percentBySliderClick(e);
			pO.au.currentTime = parseInt((percent / 100) * pO.au.duration);
		});

		this.muteBtn.addEventListener("click", function(e) {
			clickSlider(pO.volumeSlider, pO.au.volume > 0? 0: pO.prevVolume * 100);
		});

		this.volumeSlider.addEventListener("click", function(e) {
			var percent = parseInt(percentBySliderClick(e));

			if (percent == 0) {
				pO.muteBtn.innerHTML = "&#x1f507;";
			} else if (percent > 0 && pO.au.volume == 0) {
				pO.muteBtn.innerHTML = "&#x1f50a;";
			}

			pO.volumeSlider.innerText = percent + "%";
			pO.volumeSlider.style.background = getLinearGradientRule("blue", "white", percent);

			pO.setVolumePercent(percent, pO.volumeSlider);
		});

		this.au.addEventListener("play", function(e) {
			pO.pauseBtn.style.background = "white";
			pO.playBtn.style.background = "grey";
			setTimeout(function(playedTrack) {if (playedTrack == pO.playlist.curTrack) {pO.playlist.updateTrackDuration(pO.playlist.curTrack)}}, 5000, pO.playlist.curTrack);
		});

		this.au.addEventListener("pause", function(e) {
			pO.pauseBtn.style.background = "grey";
			pO.playBtn.style.background = "white";
		});

		this.au.addEventListener("timeupdate", function(e) {
			if (!pO.au.duration || pO.au.duration < 1) { return; }
			var playedPercent = (pO.au.currentTime / pO.au.duration) * 100;
			pO.durationTimer.innerText = formatSecToMin(parseInt(pO.au.currentTime)) + "/" + formatSecToMin(parseInt(pO.au.duration));
			pO.durationSlider.style.background = "linear-gradient(to right, orange " + playedPercent + "%, white " + playedPercent + "%)";
		});

		this.au.addEventListener("ended", function(e) {
			if (pO.radioMode) {
				var xhr = getXhr("GET", "/radio");
				xhr.onload = function() {
					if (xhr.readyState == 4 && xhr.status == 200) {
						 try {
							data = JSON.parse(xhr.response);
							if (!data || !data['track']) {
								pO.switchMode('none');
								return alert('Произошла ошибка. Режим "Радио" будет выключен. Попробуйте обновить страницу.');
							}
							pO.playlist.queue_clear();
							pO.playlist.addTrack(data.track.id, data.track.url, data.track.fullname, data.track.artist, data.track.album, data.track.albumYear, data.track.title, data.track.duration, data.track.sourceData);
							pO.playlist.play(pO.playlist.queue[0]);
						} finally { }
					} else {
						alert("Произошла ошибка. Попробуйте позже.");
					}
				}
			} else {
				pO.nextBtn.dispatchEvent(new Event("click"));
			}
		});

		this.pauseBtn.addEventListener("click", function(e) {
			pO.pause();
		});

		this.playBtn.addEventListener("click", function(e) {
			pO.play();
		});

		this.switchMode = function(mode) {
			switch (mode) {
				case 'repeat':
					pO.repeatMode = !this.repeatMode;
					pO.randomMode = false;
					pO.radioMode = false;
					break;
				case 'random':
					pO.repeatMode = false;
					pO.randomMode = !this.randomMode;
					pO.radioMode = false;
					break;
				case 'radio':
					if (pO.radioMode) {
						if (confirm('Отключить радио?')) {
							pO.radioMode = false;
						}
					} else {
						if (confirm('Включить радио?')) {
							pO.radioMode = true;
							pO.repeatMode = false;
							pO.randomMode = false;
							pO.au.dispatchEvent(new Event("ended"));
						}
					}
					break;
				case 'none':
					pO.radioMode = false;
					pO.repeatMode = false;
					pO.randomMode = false;
			}

			pO.repeatBtn.style.background = pO.repeatMode? "grey": "";
			pO.randomBtn.style.background = pO.randomMode? "grey": "";
			pO.radioBtn.style.background = pO.radioMode? "grey": "";
		}

		this.repeatBtn.addEventListener("click", function(e) {
			pO.switchMode("repeat");
		});

		this.randomBtn.addEventListener("click", function(e) {
			pO.switchMode("random");
		});

		this.radioBtn.addEventListener("click", function(e) {
			pO.switchMode("radio");
		});

		this.nextBtn.addEventListener("click", function(e) {
			var nextTrack;
			if (pO.radioMode) {
				pO.au.dispatchEvent(new Event("ended"));
				return;
			} else if (pO.randomMode) {
				 nextTrack = pO.playlist.getRndTrack();
			} else {
				nextTrack = pO.playlist.getNextTrack(pO.playlist.curTrack);

				if (pO.repeatMode && !nextTrack) {
					nextTrack = pO.playlist.queue.length > 0? pO.playlist.queue[0]: null;
				}
			}

			if (nextTrack) {
				pO.playlist.play(nextTrack);
			} else {
				pO.pauseBtn.dispatchEvent(new Event("click"));
			}
		});

		this.prevBtn.addEventListener("click", function(e) {
			var prevTrack;
			if (pO.radioMode) {
				pO.au.dispatchEvent(new Event("ended"));
				return;
			} else if (pO.randomMode) {
				prevTrack = pO.playlist.getRndTrack();
			} else {
				prevTrack = pO.playlist.getPrevTrack(pO.playlist.curTrack);
			}

			if (prevTrack) {
				pO.playlist.play(prevTrack);
			} else {
				pO.pauseBtn.dispatchEvent(new Event("click"));
			}
		});

		navigator.mediaSession.setActionHandler("nexttrack", function(e) {
			pO.nextBtn.dispatchEvent(new Event("click"));
		});
		navigator.mediaSession.setActionHandler("previoustrack", function(e) {
			pO.prevBtn.dispatchEvent(new Event("click"));
		});
		navigator.mediaSession.setActionHandler("seekto", function(e) {
		});
		navigator.mediaSession.setActionHandler("seekforward", function(e) {
			clickSlider(pO.durationSlider, ((pO.au.currentTime / pO.au.duration) * 100) + 1);
		});
		navigator.mediaSession.setActionHandler("seekbackward",	function(e) {
			clickSlider(pO.durationSlider, ((pO.au.currentTime / pO.au.duration) * 100) - 1);
		});

		this.playlist = function() {
			return {
				init: function() {
					if (pO.playlist) { return pO.playlist };
					pO.playlist = this;
					pO.playlist.queue = [];
					pO.playlist.curTrackIdx = -1;
					pO.playlist.renderLayout = dqs("#workplace_playlist_current");

					pO.playlist.renderLayout.addEventListener("click", function(e) {
						if (e.target.classList.contains("playlist-track-btn")) {
							var clickedIdx = parseInt(e.target.parentNode.parentNode.dataset.plIdx);

							if (e.target.classList.contains("playlist-track-btn-rm")) {
								pO.playlist.queue_remove(clickedIdx);
							} else if (e.target.classList.contains("playlist-track-btn-up")) {
								pO.playlist.queue_up(clickedIdx);
							} else if (e.target.classList.contains("playlist-track-btn-dn")) {
								pO.playlist.queue_down(clickedIdx);
							} else if (e.target.classList.contains("playlist-track-btn-pl")) {
								pO.playlist.play(pO.playlist.queue[clickedIdx]);
							}
						} else if (e.target.classList.contains("playlist-clear")) {
							pO.playlist.queue_clear();
						} else if (e.target.classList.contains("playlist-shuffle")) {
							pO.playlist.queue_shuffle();
						} else if (e.target.classList.contains("playlist-reverse")) {
							pO.playlist.queue_reverse();
						}
					});

					return pO.playlist;
				},
				_render: function() {
					pO.playlist.renderLayout.innerHTML = "<h2>Играет у " + (getCookie('user') || "?") + "</h2><div class='mb02'><button class='playlist-act-btn playlist-clear'>Очистить &cross;</button><button class='playlist-act-btn playlist-shuffle'>Перемешать &#128256;</button><button class='playlist-act-btn playlist-reverse'>Перевернуть &#8634;</button></div>";
					for (var i = 0; i < pO.playlist.queue.length; i++) {
						var elem = document.createElement('div');
						if (pO.playlist.queue[i].selected) {
							elem.id = "playlist-cur-track";
							elem.appendChild(dqs("#player_track_duration_timer").cloneNode());
						}

						elem.innerHTML = "<a href='/" + (pO.playlist.queue[i].sourceData.startsWith('album')? "album": "artist") + "/" + pO.playlist.queue[i].sourceData.split('_')[1] + "#track-" + pO.playlist.queue[i].id + "'>" + pO.playlist.queue[i].fullname + "</a>" + (pO.playlist.queue[i].duration? ("<span style='margin-left: 0.5em;'>" + pO.playlist.queue[i].duration + "</span>"): "");
						elem.innerHTML += "<div><button class='playlist-track-btn playlist-track-btn-pl'" + (pO.playlist.queue[i].selected? " disabled": "") + ">&vrtri;</button><button class='playlist-track-btn playlist-track-btn-rm'>&#x292B;</button><button class='playlist-track-btn playlist-track-btn-up'" + (i == 0? " disabled": "") + ">&uarr;</button><button class='playlist-track-btn playlist-track-btn-dn'" + (i == pO.playlist.queue.length - 1? " disabled": "") + ">&darr;</button></div>";
						elem.dataset.plIdx = i;
						elem.dataset.id = pO.playlist.queue[i].id;
						elem.dataset.filePath = pO.playlist.queue[i].url;
						elem.dataset.album = pO.playlist.queue[i].album;
						elem.dataset.albumYear = pO.playlist.queue[i].albumYear;
						elem.dataset.sourceData = pO.playlist.queue[i].sourceData;

						pO.playlist.renderLayout.appendChild(elem);
					}
				},
				queue_clear: function() { pO.playlist.queue = []; pO.playlist._render(); },
				queue_add: function(track) { pO.playlist.queue.push(track); pO.playlist._render(); },
				queue_shuffle: function() {
					var qnt = null;
					var idx = null;
					var tmp = null;
					var genIdx = function() { idx = (Math.floor(Math.random() * pO.playlist.queue.length)); return idx; };
					var new_order = [];
					for (var i = 0; i < pO.playlist.queue.length; i++) {
						qnt = 0;
						while (new_order.indexOf(genIdx()) > -1) {
							qnt++;
							if (qnt > 1000) {
								idx = new_order.length - 1;
							}
						}
						new_order.push(idx);
					}

					for (var i = 0; i < new_order.length; i++) {
						new_order[i] = pO.playlist.queue[new_order[i]];
					}

					pO.playlist.queue = new_order;

					pO.playlist._render();
				},
				queue_reverse: function() {
					pO.playlist.queue.reverse();

					pO.playlist._render();
				},
				queue_remove: function(plIdx) {
					pO.playlist.queue.splice(plIdx, 1);

					pO.playlist._render();
				},
				queue_up: function(plIdx) {
					pO.playlist.queue_swap(plIdx, plIdx - 1)
				},
				queue_down: function(plIdx) {
					pO.playlist.queue_swap(plIdx, plIdx + 1)
				},
				queue_swap: function(plIdxOld, plIdxNew) {
					if (plIdxNew > pO.playlist.queue.length - 1 || plIdxNew < 0) { return; }
					var swapped = pO.playlist.queue[plIdxNew];
					pO.playlist.queue[plIdxNew] = pO.playlist.queue[plIdxOld];
					pO.playlist.queue[plIdxOld] = swapped;

					pO.playlist._render();
				},
				play: function(track) {
					pO.setTrack(track);
					pO.playlist.setSelectedTrack(track);

					pO.playlist._render();
				},
				addTrack: function(id, url, fullname, artist, album, albumYear, title, duration, sourceData) {
					pO.playlist.queue_add({'id': id, 'url': url, 'fullname': fullname, 'artist': artist, 'album': album, 'albumYear': albumYear, 'title': title, 'duration': duration, 'sourceData': sourceData});
				},
				updateTrackDuration: function(track, duration) {
					if (!track.duration && duration) {
						track.duration = formatSecToMin(parseInt(duration));
						if (dqs("#load-album")) {
							dqs("#load-album").click();
						} else if (dqs("#load-artist")) {
							dqs("#load-artist").click();
						}
					} else if (!track.duration && pO.au.duration) {
						var xhr = getXhr("GET", "/track/setduration", {'id': track.id, 'duration': pO.au.duration});
						xhr.onload = function() {
							if (xhr.readyState == 4 && xhr.status == 200) {
								 try {
									data = JSON.parse(xhr.response);
									pO.playlist.updateTrackDuration(track, data['duration']);
								} finally { }
							} else {
								alert("Произошла ошибка. Попробуйте позже.");
							}
						}
					}
					pO.playlist._render();
				},
				setSelectedTrack: function(track) {
					track.selected = true;
					for (var i = 0; i < pO.playlist.queue.length; i++) {
						if (pO.playlist.queue[i] != track) {
							pO.playlist.queue[i].selected = false;
						} else {
							pO.playlist.curTrack = pO.playlist.queue[i];
							pO.playlist.curTrackIdx = i;
						}
					}

				},
				getNextTrack: function(track) {
					for (var i = 0; i < pO.playlist.queue.length; i++) {
						if (pO.playlist.queue[i] == track) {
							return (i < pO.playlist.queue.length - 1? pO.playlist.queue[i + 1]: null);
						}
					}
				},
				getPrevTrack: function(track) {
					for (var i = 0; i < pO.playlist.queue.length; i++) {
						if (pO.playlist.queue[i] == track) {
							return (i != 0 ? pO.playlist.queue[i-1]: null);
						}
					}
				},
				getRndTrack: function() {
					if (pO.playlist.queue.length < 2) { return null; }

					var track = null;
					while (!track || track == pO.playlist.curTrack) {
						track = pO.playlist.queue[Math.floor(Math.random() * (pO.playlist.queue.length))];
					}

					return track;
				}
			}
		}().init();

		clickSlider(this.volumeSlider, 100);

		return pO;
	},
	exist: function() { return Boolean(this.au) },
	play: function() {
		if (!this.au.src || this.au.src.slice(-4).toLowerCase() != ".mp3") { return; }
		this.au.play();
	},
	pause: function() {
		this.au.pause();
	},
	setTrack: function(track, paused) {
		this.au.src = track.url;
		if (!paused) { this.play(); }
		dqs("#player_audio_data_artist").innerText = track.artist;
		var albumTitle = track.album || "-";
		if (track.album && track.albumYear) {
			albumTitle += " (" + track.albumYear + ")"
		}
		dqs("#player_audio_data_album").innerText = albumTitle;
		dqs("#player_audio_data_track").innerText = track.title;
		navigator.mediaSession.metadata = new MediaMetadata({
			"title": track.title,
			"artist": track.artist,
			"album": track.album || "-",
		});
	},
	setVolumePercent: function(volPercent, source) {
		if (volPercent < 0 || volPercent > 100) { return; }
		this.prevVolume = this.au.volume;
		this.au.volume = volPercent / 100;
		if (!source || source != this.volumeSlider) {
			clickSlider(this.volumeSlider, volPercent);
		}
	}
}

var formatSecToMin = function(sec) { return ("0" + ((sec - sec % 60) / 60)).slice(-2) +  ":" + ("0" + sec % 60).slice(-2) }

var percentBySliderClick = function(event) {
	var ret = (100 * (event.clientX / (event.target.getBoundingClientRect().right - event.target.getBoundingClientRect().left - 10)));
	if (ret > 100) { ret = 100 }
	else if (ret < 0) { ret = 0 }

	return ret;
}

var getLinearGradientRule = function(c1, c2, progressPercent) {
	return "linear-gradient(to right, " + c1 + " " + progressPercent + "%, " + c2 + " " + progressPercent + "%)"
}

var clickSlider = function(sliderElem, percent) {
	sliderElem.dispatchEvent(function() {
		var evt = new Event("click");
		evt.clientX = (parseInt(percent) * (sliderElem.getBoundingClientRect().right)) / 100;

		return evt;
	}());
}

function getXhr(method, href, params, onerrorFunc) {
	var xhr = new XMLHttpRequest();
	if (method == "GET" && params ) {
		href = href + "?";
		for (var k in params) {
			href += k + "=" + params[k] + "&";
		}
		href = href.slice(0, -1);
	}
	xhr.open(method, href);
	xhr.setRequestHeader('X-Shamus', 'shamus');
	xhr.send();

	if (!onerrorFunc) {
		xhr.onerror = function() {
			alert("Произошла ошибка. Попробуйте позже.");
		}
	} else {
		xhr.onerror = onerrorFunc;
	}

	return xhr;
}

var selectQsField = {
	init: function(formField, mdl) {
		var sqsf = dqs("#" + formField.id + "_search_block");
		if (sqsf) { return sqsf; }

		var sqsf = this;

		this.formField = formField;
		this.mdl = mdl;

		this.searchBlock = document.createElement("div");
		this.queryInputElem = document.createElement("input");
		this.queryInputElem.size = 25;
		this.queryInputElem.type = "text";
		this.resultTableElem = document.createElement("table");
		this.resultTableElem.innerHTML = "<table><tr><th style='min-width:15em;'>Выбрано:</th><th style='min-width:15em;'>Поиск:</th></tr><tr><td></td><td></td></tr></table>";
		this.searchBlock.append(this.resultTableElem);
		this.resultTableElem.rows[1].cells[1].append(this.queryInputElem);
		this.searchBlock.id = formField.id + "_search_block";
		this.selected = {};
		this.searchRes = [];

		this.queryInputElem.addEventListener("input", function(e) {
			var curVal = e.target.value;
			if (curVal) {
				setTimeout(function() { if (sqsf.queryInputElem.value == curVal) { sqsf._search(e.target.value); } }, 500);
			} else {
				sqsf.searchRes = [];
				sqsf._render("clearSearchRes");
			}
		});

		this._render("init");

		return this;
	},
	_render: function(step, data) {
		var sqsf = this;

		if (step == "init") {
			this.formField.style.display = "none";
			this.formField.parentNode.insertBefore(this.searchBlock, this.formField);
				this.resultTableElem.rows[1].cells[1].addEventListener("click", function(e) {
				if (e.target.classList.contains("link-btn")) {
					var isSelected = e.target.dataset.id in sqsf.selected;

					if (!isSelected) {
						sqsf.selected[e.target.dataset.id] = e.target.innerText;
						sqsf._render("select");
					}
				}
			});

			while (this.formField.options.length > 0) {
				if (this.formField.options[this.formField.options.length - 1].selected) {
					this.selected[this.formField.options[this.formField.options.length - 1].value] = this.formField.options[this.formField.options.length -1].innerText;
				}

				this.formField.options[this.formField.options.length - 1].remove();
			}

			this._render("select");
		} else if (step == "searchres") {
			this._render("clearSearchRes");

			for (var i = 0; i < this.searchRes.length; i++) {
				var d = document.createElement("div");
				d.dataset.id = Object.keys(this.searchRes[i])[0];
				d.innerText = this.searchRes[i][d.dataset.id] + " [+]";
				d.classList.add("link-btn");
				this.resultTableElem.rows[1].cells[1].appendChild(d);
			}
		} else if (step == "clearSearchRes") {
			while (this.resultTableElem.rows[1].cells[1].childNodes.length > 1) {
				this.resultTableElem.rows[1].cells[1].childNodes[1].remove();
			}
		} else if (step == "select") {
			for (var selectLineId in this.selected) {
				var isSelected = false;
				for (var j = 0; j < this.resultTableElem.rows[1].cells[0].childNodes.length; j++) {
					if (selectLineId == this.resultTableElem.rows[1].cells[0].childNodes[j].dataset.id) {
						isSelected = true;
						break;
					}
				}

				if (!isSelected) {
					var d = document.createElement("div");
					d.classList.add("link-btn");
					d.dataset.id = selectLineId;
					d.innerText = this.selected[selectLineId].replace("[+]", "[x]");
					this.resultTableElem.rows[1].cells[0].appendChild(d);

					d.addEventListener("click", function(e) {
						for (var i = 0; i < sqsf.formField.options.length; i++) {
							if (sqsf.formField.options[i].value == e.target.dataset.id) {
								sqsf.formField.options[i].remove();
								break;
							}
						}

						if (e.target.dataset.id in sqsf.selected) {
							delete sqsf.selected[e.target.dataset.id];
						}

						e.target.remove();
					});

					var opt = document.createElement("option");
					opt.value = d.dataset.id;
					opt.innerText = d.innerText;
					opt.selected = true;
					this.formField.appendChild(opt);
				}
			}
		}
	},
	_search: function(query) {
		if (!query) {
			return;
		}

		var xhr = getXhr("GET", "/search/field", {[this.mdl]: query});
		var sqsf = this;
		xhr.onload = function() {
			if (xhr.readyState == 4 && xhr.status == 200) {
				try {
					data = JSON.parse(xhr.response);

					sqsf.searchRes = [];
					for (var d in data) {
						sqsf.searchRes.push({[d]: data[d]});
					}

					sqsf._render("searchres");
				} finally { }
			} else {
				alert("Произошла ошибка. Попробуйте позже.");
			}
		}
	}
}

var player = player.init();

document.body.addEventListener("click", function(e) {
	if (!dqs("#workplace_main")) {
		return;
	}

	if (e.target.dataset.filePath && e.target.classList.contains("to-current-playlist")) {
		player.playlist.addTrack(e.target.dataset.id, e.target.dataset.filePath, e.target.dataset.fileFullName, e.target.dataset.artist, e.target.dataset.album, e.target.dataset.albumYear, e.target.dataset.title, e.target.dataset.duration, e.target.dataset.sourceData);
	} else if (e.target.tagName.toLowerCase() == "a" && !e.target.target) {
		e.preventDefault();
		if (!e.target.href) { return; }
		var xhr = getXhr("GET", e.target.href);
		xhr.onload = function() {
			if (xhr.readyState == 4 && xhr.status == 200) {
				if (xhr.responseURL.search('/login') > 0) {
					window.location = xhr.responseURL;
				}
				window.history.pushState({'render_data': xhr.response}, "", e.target.href);
				dqs("#workplace_main").innerHTML = xhr.response;
				if (window.location.hash) {
					var hashElem = dqs(window.location.hash);
					if (hashElem) {
						var coords = hashElem.parentNode.getBoundingClientRect();
						window.scrollTo(coords.x, coords.y)
					}
				}

				var titleCookie = getCookie('shamus-title', true);
				document.title = "ShaMus" + (titleCookie? (" | " + titleCookie): "");
			} else {
				alert("Произошла ошибка. Попробуйте позже.");
			}
		}
	} else if (e.target.classList.contains("to-current-playlist-list")) {
		if (e.target.nextSibling.classList.contains("tracklist")) {
			var toTracklistBtns = e.target.nextSibling.querySelectorAll(".to-current-playlist");
			for (var i = 0; i < toTracklistBtns.length; i++) {
				toTracklistBtns[i].dispatchEvent(new MouseEvent("click", {"bubbles": true}));
			}
		}
	} else if (e.target.classList.contains("to-current-playlist-by-title")) {
		var href = e.target.dataset.source.split('_').slice(-1) + "/tracklist/";
		if (e.target.dataset.source.startsWith("album")) {
			href = "/album/" + href;
		} else if (e.target.dataset.source.startsWith("artist")) {
			href = "/artist/" + href;
		}
		var xhr = getXhr("GET", href);
		xhr.onload = function() {
			if (xhr.readyState == 4 && xhr.status == 200) {
				if (xhr.responseURL.search("/login") > 0) {
					window.location = xhr.responseURL;
				}

				data = JSON.parse(xhr.response);
				if (!data || !data["tracklist"]) {
					return alert('Произошла ошибка. Попробуйте обновить страницу.');
				}

				for (var i = 0; i < data["tracklist"].length; i++) {
					player.playlist.addTrack(data["tracklist"][i].id, data["tracklist"][i].url, data["tracklist"][i].fullname, data["tracklist"][i].artist, data["tracklist"][i].album, data["tracklist"][i].albumYear, data["tracklist"][i].title, data["tracklist"][i].duration, data["tracklist"][i].sourceData);
				}
			}
		}
	}
});

var orderAlbumField = {
	init: function() {
		var atTbl = dqs("#album_tracks");
		var utTbl = dqs("#unalbum_tracks");
		var otInp = dqs("#id_track_order");
		if (!atTbl || !utTbl || !otInp) { return; }
		this.atTbl = atTbl;
		this.utTbl = utTbl;
		this.otInp = otInp;
		var that = this;

		/* id | fileName | rowChecked */
		this.album_tracks = [];
		for (var i = 1; i < atTbl.rows.length; i++) {

			this.album_tracks.push([atTbl.rows[i].cells[2].dataset.id, atTbl.rows[i].cells[2].textContent, false]);
		}

		this.unalbum_tracks = [];
		for (var i = 1; i < utTbl.rows.length; i++) {
			this.unalbum_tracks.push([utTbl.rows[i].cells[2].dataset.id, utTbl.rows[i].cells[2].textContent, false]);
		}

		atTbl.addEventListener("click", function(e) {
			var trg = e.target;

			if (trg.parentNode.rowIndex != 0 && trg.tagName.toLowerCase() == "input") {
				if (trg.checked) {
					trg.parentNode.parentNode.style.backgroundColor = "lightskyblue";
					that.album_tracks[trg.parentNode.parentNode.rowIndex - 1][2] = true;
				} else {
					trg.parentNode.parentNode.style.backgroundColor = "";
					that.album_tracks[trg.parentNode.parentNode.rowIndex - 1][2] = false;
				}
			}
			else if (trg.parentNode.parentNode.rowIndex == 0) {
				if (trg.dataset.act == "unselect") {
					for (var i = 1; i < that.atTbl.rows.length; i++) {
						that.atTbl.rows[i].cells[0].childNodes[0].checked? that.atTbl.rows[i].cells[0].childNodes[0].click(): null;
					}
				} else if (trg.dataset.act == "up" || trg.dataset.act == "down") {
					var shiftIdx = trg.dataset.act == "up"? 1: -1;
					for (var i = 1; i < that.atTbl.rows.length; i++) {
						if (that.atTbl.rows[i].cells[0].childNodes[0].checked) {
							var curPos = i - 1;
							if ((curPos == 0 && shiftIdx == 1) || (curPos == that.album_tracks.length -1 && shiftIdx == -1)) continue;

							var tmp = that.album_tracks[curPos - shiftIdx];
							that.album_tracks[curPos - shiftIdx] = that.album_tracks[curPos];
							that.album_tracks[curPos] = tmp;
						}
					}

					that._render();
				} else if (trg.dataset.act == "delete") {
					var removedIdx = [];

					for (var i = 1; i < that.atTbl.rows.length; i++) {
						if (that.atTbl.rows[i].cells[0].childNodes[0].checked) {
							that.album_tracks[i-1][2] = false;
							removedIdx.push(that.album_tracks[i-1][0]);
							that.unalbum_tracks.push(that.album_tracks[i-1]);
						}
					}

					var tmp = [];
					for (var i = 0; i < that.album_tracks.length; i++) {
						removedIdx.includes(that.album_tracks[i][0])? null: tmp.push(that.album_tracks[i]);
					}
					that.album_tracks = tmp;

					that._render();
				}
			}
		});

		utTbl.addEventListener("click", function(e) {
			var trg = e.target;

			if (trg.tagName.toLowerCase() == "input") {
				if (trg.checked) {
					trg.parentNode.parentNode.style.backgroundColor = "lightskyblue";
					that.unalbum_tracks[trg.parentNode.parentNode.rowIndex - 1][2] = true;
				} else {
					trg.parentNode.parentNode.style.backgroundColor = "";
					that.unalbum_tracks[trg.parentNode.parentNode.rowIndex - 1][2] = false;
				}
			} else if (trg.parentNode.parentNode.rowIndex == 0) {
				if (trg.dataset.act == "unselect") {
					for (var i = 1; i < that.utTbl.rows.length; i++) {
						that.utTbl.rows[i].cells[0].childNodes[0].checked? that.utTbl.rows[i].cells[0].childNodes[0].click(): null;
					}
				}
				else if (trg.dataset.act == "push") {
					var removedIdx = [];

					for (var i = 1; i < that.utTbl.rows.length; i++) {
						if (that.utTbl.rows[i].cells[0].childNodes[0].checked) {
							that.unalbum_tracks[i-1][2] = false;
							removedIdx.push(that.unalbum_tracks[i-1][0]);
							that.album_tracks.push(that.unalbum_tracks[i-1]);
						}
					}

					var tmp = [];
					for (var i = 0; i < that.unalbum_tracks.length; i++) {
						removedIdx.includes(that.unalbum_tracks[i][0])? null: tmp.push(that.unalbum_tracks[i]);
					}
					that.unalbum_tracks = tmp;

					that._render();
				}
			}
		});
	},
	_render: function() {
		var that = this;

		var redrawTbl = function(tbl, data) {
			tbl.innerHTML = tbl.rows[0].innerHTML;
			for (var i = 0; i < data.length; i++) {
				var tr = document.createElement("tr");
				tr.innerHTML = "<td class='center' style='width: 5em;'><input type='checkbox' /></td><td class='center' style='width: 5em;'>" + (i + 1) + "</td><td data-id='" + data[i][0] + "' colspan='2'>" + data[i][1] + "</td>";
				tbl.appendChild(tr);

				data[i][2]? tr.cells[0].childNodes[0].click(): null;				
			}
		}

		redrawTbl(this.atTbl, this.album_tracks);
		redrawTbl(this.utTbl, this.unalbum_tracks);
		this.otInp.value = (function() { var r = []; for (var i = 0; i < that.album_tracks.length; i++) { r.push(that.album_tracks[i][0]) } return r; }()).join(",") + ",";
	}
}

orderAlbumField.init();

var uploadField = dqs("#id_file_field");
if (uploadField) {
	var selectedFilesList = dqs("#selected_files");
	if (uploadField) {
		if (!selectedFilesList) {
			selectedFilesList = document.createElement("ul");
			selectedFilesList.style.marginLeft = "1.5em";
			uploadField.parentNode.appendChild(selectedFilesList);
		}

		uploadField.addEventListener("change", function(e) {
			selectedFilesList.innerHTML = "";
			dqs("#id_upload").disabled = false;
			for (var i = 0; i < uploadField.files.length; i++) {
				var fl = document.createElement("li");
				fl.innerText = uploadField.files[i].name;
				if (fl.innerText.slice(-4).toLowerCase() != ".mp3") {
					fl.style.color = "red";
					dqs("#id_upload").disabled = true;
				}
				selectedFilesList.appendChild(fl);
			}
		});

		uploadField.dispatchEvent(new Event("change"));
	}
}

var searchQsFields = document.getElementsByClassName("sfqs");
for (var i = 0; i < searchQsFields.length; i++) {
	var mdl_id = "";
	if (searchQsFields[i].id == "id_artist") {
		mdl_id = "artist";
	} else if (searchQsFields[i].id == "id_genre") {
		mdl_id = "genre";
	}
	selectQsField.init(searchQsFields[i], mdl_id);
}

window.addEventListener("popstate", function(e) {
	dqs("#workplace_main").innerHTML = e.state.render_data;
});
