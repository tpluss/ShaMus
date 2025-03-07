var dqs = function(selector) { return document.querySelector(selector); }

function getCookie(name) {
	var matches = document.cookie.match(new RegExp(
		"(?:^|; )" + name.replace(/([\.$?*|{}\(\)\[\]\\\/\+^])/g, '\\$1') + "=([^;]*)"
	));

	return matches ? decodeURIComponent(matches[1]) : undefined;
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
		this.repeatMode = false;
		this.randomMode = false;

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
			pO.nextBtn.dispatchEvent(new Event("click"));
		});

		this.pauseBtn.addEventListener("click", function(e) {
			pO.pause();
		});

		this.playBtn.addEventListener("click", function(e) {
			pO.play();
		});

		this.repeatBtn.addEventListener("click", function(e) {
		   if (pO.randomMode) {
				pO.randomBtn.dispatchEvent(new Event("click"));
			}
			pO.repeatMode = !pO.repeatMode;
			pO.repeatBtn.style.background = pO.repeatMode? "grey": "";

		});

		this.randomBtn.addEventListener("click", function(e) {
			if (pO.repeatMode) {
				pO.repeatBtn.dispatchEvent(new Event("click"));
			}                    
			pO.randomMode = !pO.randomMode;
			pO.randomBtn.style.background = pO.randomMode? "grey": "";
		});

		this.nextBtn.addEventListener("click", function(e) {
			var nextTrack;                    
			if (pO.randomMode) {
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
			if (pO.randomMode) {
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
						} else if (e.target.classList.contains("clear-playlist")) {
							pO.playlist.queue_clear();
						}
					});

					return pO.playlist;
				},
				_render: function() {
					pO.playlist.renderLayout.innerHTML = "<h2>Играет у " + getCookie('user') || '?' + "</h2><div><button class='clear-playlist'>[Очистить]</button></div>";
					for (var i = 0; i < pO.playlist.queue.length; i++) {
						var elem = document.createElement('div');
						if (pO.playlist.queue[i].selected) {
							elem.id = "playlist-cur-track";
							elem.appendChild(dqs("#player_track_duration_timer").cloneNode());
						}
						elem.innerHTML = "<span>" + pO.playlist.queue[i].fullname + "</span>" + (pO.playlist.queue[i].duration? ("<span style='margin-left: 0.5em;'>" + pO.playlist.queue[i].duration + "</span>"): "");
						elem.innerHTML += "<div><button class='playlist-track-btn playlist-track-btn-pl'" + (pO.playlist.queue[i].selected? " disabled": "") + ">&vrtri;</button><button class='playlist-track-btn playlist-track-btn-rm'>&#x292B;</button><button class='playlist-track-btn playlist-track-btn-up'>&uarr;</button><button class='playlist-track-btn playlist-track-btn-dn'>&darr;</button></div>";
						elem.dataset.plIdx = i;
						elem.dataset.id = pO.playlist.queue[i].id
						elem.dataset.filePath = pO.playlist.queue[i].url;
						elem.dataset.album = pO.playlist.queue[i].album;

						pO.playlist.renderLayout.appendChild(elem);
					}
				},
				queue_clear: function() { pO.playlist.queue = []; pO.playlist._render(); },
				queue_add: function(track) { pO.playlist.queue.push(track); pO.playlist._render(); },
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
				addTrack: function(id, url, fullname, artist, album, title, duration) {
					pO.playlist.queue_add({'id': id, 'url': url, 'fullname': fullname, 'artist': artist, 'album': album, 'title': title, 'duration': duration});
				},
				updateTrackDuration: function(track, duration) {
					if (!track.duration && duration) {
						track.duration = formatSecToMin(parseInt(duration));
						dqs("#load-album").click();
					} else if (!track.duration && pO.au.duration) {
						var xhr = getXhr("GET", "{% url 'track-set-duration' %}", {'id': track.id, 'duration': pO.au.duration});
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
		dqs("#player_audio_data_album").innerText = track.album || "-";
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
	return (100 * (event.clientX / (event.target.getBoundingClientRect().right - event.target.getBoundingClientRect().left - 10)))
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

player.init();

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

document.body.addEventListener("click", function(e) {
	if (e.target.dataset.filePath && e.target.classList.contains("to-current-playlist")) {
		player.playlist.addTrack(e.target.dataset.id, e.target.dataset.filePath, e.target.dataset.fileFullName, e.target.dataset.artist, e.target.dataset.album, e.target.dataset.title, e.target.dataset.duration);
	} else if (e.target.tagName.toLowerCase() == "a" && !e.target.target) {
		e.preventDefault();
		if (!e.target.href) { return; }       
		var xhr = getXhr("GET", e.target.href);
		xhr.onload = function() {
			if (xhr.readyState == 4 && xhr.status == 200) {
				if (xhr.responseURL.search('/login') > 0) {
					window.location = xhr.responseURL;
				}
				dqs("#workplace_main").innerHTML = xhr.response;
				window.history.pushState({'render_data': xhr.response}, "", e.target.href);
			} else {
				alert("Произошла ошибка. Попробуйте позже.");
			} 
		}
	} else if (e.target.classList.contains("to-current-playlist-list")) {
		for (var i = 1; i < e.target.nextSibling.nextSibling.childNodes.length; i += 2) {
			if (e.target.nextSibling.nextSibling.childNodes[i]) {
				e.target.nextSibling.nextSibling.childNodes[i].childNodes[7].dispatchEvent(new MouseEvent("click", {"bubbles": true}));
			}
		}
	}
});

var orderAlbumField = {
	init: function() {
		var atf = dqs("#album_tracks");
		var utf = dqs("#unalbumed_tracks");
		var otf = dqs("#id_track_order");
		if (!atf || !utf || !otf) { return; }
		this.atf = atf;
		this.utf = utf;
		this.otf = otf;
		var that = this;

		this.album_tracks = [];
		for (var i = 0; i < atf.childNodes.length; i++) {
			this.album_tracks.push([atf.childNodes[i].dataset.id, atf.childNodes[i].childNodes[0].textContent]);
		}
		this.unalbumed_tracks = [];
		for (var i = 0; i < utf.childNodes.length; i++) {
			this.unalbumed_tracks.push([utf.childNodes[i].dataset.id, utf.childNodes[i].childNodes[0].textContent]);
		}

		this._render();

		utf.addEventListener("click", function(e) {
			e.preventDefault();
			if (e.target.tagName.toLowerCase() == "button") {
				if (e.target.dataset.act == "add") {
					var mve = e.target.parentNode.cloneNode(true);
					that.atf.appendChild(mve);
					e.target.parentNode.remove();
					mve.classList.add("green");
				}

				that._render();
			}
		});

		otf.addEventListener("change", function(e) {
			e.target.value = e.target.value.replaceAll(" ", "");
			if (e.target.value.slice(-1) != ",") {
				e.target.value += ",";
			}

			ids = e.target.value.slice(0, -1).split(",");
			for (var i = 0; i < ids.length; i++) {
				if (!that.album_tracks.includes("" + ids[i]) && !that.unalbumed_tracks.includes("" + ids[i])) {
					return alert("Трек с id = " + ids[i] + " не относится к данному исполнителю!");
				}
			}

			this._render();
		});

		atf.addEventListener("click", function(e) {
			e.preventDefault();
			if (e.target.tagName.toLowerCase() == "button") {
				if (e.target.dataset.act == "up") {
					for (var i = 0; i < that.album_tracks.length; i++) {
						if (e.target.parentNode.dataset.id == that.album_tracks[i][0]) {
							if (i == 0) { break }
							var swp = that.album_tracks[i-1];
							that.album_tracks[i-1] = that.album_tracks[i];
							that.album_tracks[i] = swp;
							break;
						}
					}
				} else if (e.target.dataset.act == "down") {
					for (var i = that.album_tracks.length - 1; i > -1; i--) {
						if (e.target.parentNode.dataset.id == that.album_tracks[i][0]) {
							if (i == that.album_tracks.length - 1) { break }
							var swp = that.album_tracks[i+1];
							that.album_tracks[i+1] = that.album_tracks[i];
							that.album_tracks[i] = swp;
							break;
						}
					}
				} else if (e.target.dataset.act == "remove") {
					for (var i = 0; i < that.album_tracks.length; i++) {
						if (e.target.parentNode.dataset.id == that.album_tracks[i][0]) {
							that.unalbumed_tracks.push(that.album_tracks[i]);
							that.album_tracks.splice(i, 1);
							break;
						}
					}
				}

				that._render();
			}
		});
	},
	_render: function() {
		var albumBtnHTML = "&nbsp;<button data-act='up' title='Выше'>&uarr;</button><button data-act='down' title='Ниже'>&darr;</button><button data-act='remove' title='Удалить из альбома'>&cross;</button>";
		var unalbumedBtnHTML = "&nbsp;<button data-act='add' title='В Альбом'>+</button>";

		this.atf.innerHTML = "";
		this.otf.value = "";
		for (var i = 0; i < this.album_tracks.length; i++) {
			var li = document.createElement("li");
			li.dataset.id = this.album_tracks[i][0];
			li.innerText = this.album_tracks[i][1];
			li.innerHTML += albumBtnHTML;
			this.atf.appendChild(li);

			this.otf.value += this.album_tracks[i][0] + ",";
		}

		this.utf.innerHTML = "";
		for (var i = 0; i < this.unalbumed_tracks.length; i++) {
			var li = document.createElement("li");
			li.dataset.id = this.unalbumed_tracks[i][0];
			li.innerText = this.unalbumed_tracks[i][1];
			li.innerHTML += unalbumedBtnHTML;
			this.utf.appendChild(li);
		}
	}
}

orderAlbumField.init();

var uploadField = dqs("#file_field_id");
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
	selectQsField.init(searchQsFields[i], "artist");
}

window.addEventListener("popstate", function(e) {
	dqs("#workplace_main").innerHTML = e.state.render_data;
});
