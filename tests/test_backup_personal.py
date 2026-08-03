"""Backing up personal/ — the part that has to work on the worst day.

WHY THESE TESTS ARE SHAPED THIS WAY: a backup is only ever exercised when something
has already gone wrong, which is the worst possible moment to discover that the
archive was empty, or that it restored over the top of good files, or that a path in
it escaped the extraction root. So every test here asks "what does this do in the
failure case", not "does the happy path run".

The tree is synthetic on purpose. Pointing these at the real personal/ would make
them pass or fail based on one machine's contents, and CI scaffolds a blank template
where that folder is nearly empty.
"""

import json
import os
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from typing import ClassVar

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "engine"))

import backup_personal as bp


class BackupTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self._tmp.name) / "repo"
        self.personal = self.repo / "personal"
        self.dest = Path(self._tmp.name) / "cloud"
        self.dest.mkdir(parents=True)
        for rel, body in (
            ("career-profile.md", "# profile\n"),
            ("userconfig.py", "NAME = 'x'\n"),
            ("data/jobs.json", '{"jobs": []}\n'),
            ("data/pipeline.md", "| id |\n"),
            ("data/leads_raw.csv", "a,b\n" * 500),
            ("applications/acme/resume.json", '{"name": "x"}\n'),
            ("applications/acme/Jon Goldberg - Resume.docx", "PK-not-really"),
            ("applications/acme/Jon Goldberg - Resume.pdf", "%PDF-not-really"),
            ("__pycache__/x.pyc", "junk"),
        ):
            p = self.personal / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(body, encoding="utf-8")

    def tearDown(self):
        self._tmp.cleanup()

    def rels(self, paths):
        return sorted(p.split("personal/", 1)[1] for p in paths)

    # ---- what goes in, and what must not silently vanish ---------------------

    def test_generated_documents_are_left_out_of_a_core_backup(self):
        inc, _ = bp.collect(str(self.personal))
        self.assertIn("career-profile.md", self.rels(inc))
        self.assertIn("applications/acme/resume.json", self.rels(inc))
        self.assertNotIn("applications/acme/Jon Goldberg - Resume.docx", self.rels(inc))
        self.assertNotIn("applications/acme/Jon Goldberg - Resume.pdf", self.rels(inc))

    def test_full_mode_keeps_the_documents_that_were_actually_sent(self):
        inc, excluded = bp.collect(str(self.personal), full=True)
        self.assertIn("applications/acme/Jon Goldberg - Resume.docx", self.rels(inc))
        self.assertEqual(excluded, [], "full mode must exclude nothing")

    def test_excluded_files_are_reported_rather_than_dropped_in_silence(self):
        # The denylist is the one place this can quietly lose something, so the
        # caller is always handed the list to print.
        _, exc = bp.collect(str(self.personal))
        self.assertTrue(exc)
        self.assertIn("applications/acme/Jon Goldberg - Resume.pdf", self.rels(exc))

    def test_an_unrecognised_file_type_is_included_not_dropped(self):
        (self.personal / "notes.org").write_text("new kind of file", encoding="utf-8")
        inc, _ = bp.collect(str(self.personal))
        self.assertIn("notes.org", self.rels(inc))

    def test_pycache_never_travels(self):
        for full in (False, True):
            inc, _ = bp.collect(str(self.personal), full=full)
            self.assertFalse([p for p in inc if "__pycache__" in p], f"full={full}")

    # ---- the archive is a restore point, or it is not a backup ---------------

    def test_paths_are_repo_relative_so_an_extract_lands_in_the_right_place(self):
        path, _ = bp.create(str(self.personal), str(self.dest))
        with zipfile.ZipFile(path) as z:
            names = [n for n in z.namelist() if n != bp.MANIFEST and n != "RESTORE.md"]
        self.assertTrue(all(n.startswith("personal/") for n in names), names[:3])

    def test_the_archive_explains_its_own_restore(self):
        path, _ = bp.create(str(self.personal), str(self.dest))
        with zipfile.ZipFile(path) as z:
            doc = z.read("RESTORE.md").decode("utf-8")
        self.assertIn("--restore", doc)
        self.assertIn("rebuild them from the .json", doc)

    def test_an_archive_missing_the_profile_says_so_loudly(self):
        (self.personal / "career-profile.md").unlink()
        path, man = bp.create(str(self.personal), str(self.dest))
        self.assertIn("personal/career-profile.md", man["missing_required"])
        self.assertFalse(bp.verify(path)["ok"])
        with zipfile.ZipFile(path) as z:
            self.assertIn("WARNING", z.read("RESTORE.md").decode("utf-8"))

    def test_an_interrupted_write_leaves_no_plausible_archive(self):
        # create() writes .partial and renames; nothing half-written should ever
        # match the glob that --list and --verify pick newest from.
        bp.create(str(self.personal), str(self.dest))
        self.assertFalse([p for p in os.listdir(self.dest) if p.endswith(".partial")])

    # ---- verification has to actually verify ---------------------------------

    def test_verify_extracts_and_rehashes_rather_than_trusting_the_manifest(self):
        path, _ = bp.create(str(self.personal), str(self.dest))
        self.assertTrue(bp.verify(path)["ok"])

    def test_a_corrupted_member_is_caught(self):
        path, _ = bp.create(str(self.personal), str(self.dest))
        man = bp.read_manifest(path)
        # Rewrite the archive with one file's contents altered but its manifest
        # hash left alone - exactly what silent bit-rot or a bad edit looks like.
        with zipfile.ZipFile(path) as z:
            members = {n: z.read(n) for n in z.namelist()}
        members["personal/career-profile.md"] = b"tampered"
        with zipfile.ZipFile(path, "w") as z:
            for n, b in members.items():
                z.writestr(n, b)
        r = bp.verify(path)
        self.assertFalse(r["ok"])
        self.assertIn("personal/career-profile.md", r["mismatched"])
        self.assertEqual(man["file_count"], r["manifest"]["file_count"])

    # ---- restore must not become the disaster ---------------------------------

    def test_restore_refuses_to_overwrite_by_default(self):
        path, _ = bp.create(str(self.personal), str(self.dest))
        target = Path(self._tmp.name) / "restored"
        (target / "personal").mkdir(parents=True)
        (target / "personal" / "career-profile.md").write_text("LOCAL EDIT", encoding="utf-8")
        written, skipped = bp.restore(path, str(target))
        self.assertIn("personal/career-profile.md", skipped)
        self.assertEqual(
            (target / "personal" / "career-profile.md").read_text(encoding="utf-8"), "LOCAL EDIT"
        )
        self.assertIn("personal/data/jobs.json", written)

    def test_force_overwrites_only_when_asked(self):
        path, _ = bp.create(str(self.personal), str(self.dest))
        target = Path(self._tmp.name) / "restored2"
        (target / "personal").mkdir(parents=True)
        (target / "personal" / "career-profile.md").write_text("LOCAL EDIT", encoding="utf-8")
        bp.restore(path, str(target), force=True)
        self.assertEqual(
            (target / "personal" / "career-profile.md").read_text(encoding="utf-8"), "# profile\n"
        )

    def test_archive_metadata_does_not_land_in_the_repo(self):
        path, _ = bp.create(str(self.personal), str(self.dest))
        target = Path(self._tmp.name) / "restored3"
        bp.restore(path, str(target))
        self.assertFalse((target / bp.MANIFEST).exists())
        self.assertFalse((target / "RESTORE.md").exists())

    def test_a_member_escaping_the_root_is_refused_on_restore_and_verify(self):
        path = self.dest / "bellows-personal-core-2026-01-01.zip"
        good = json.dumps(
            {
                "format_version": 1,
                "mode": "core",
                "files": [],
                "file_count": 0,
                "created": "x",
                "repo": "r",
                "total_bytes": 0,
                "excluded_count": 0,
                "missing_required": [],
            }
        )
        with zipfile.ZipFile(path, "w") as z:
            z.writestr(bp.MANIFEST, good)
            z.writestr("../escaped.txt", "no")
        target = Path(self._tmp.name) / "restored4"
        written, skipped = bp.restore(str(path), str(target))
        self.assertEqual(written, [])
        self.assertTrue(any("unsafe" in s for s in skipped), skipped)
        self.assertFalse((Path(self._tmp.name) / "escaped.txt").exists())
        self.assertFalse(bp.verify(str(path))["ok"])

    # ---- retention ------------------------------------------------------------

    def test_prune_keeps_the_newest_and_never_empties_the_folder(self):
        made = []
        for i in range(5):
            p = self.dest / f"bellows-personal-core-2026-01-0{i + 1}.zip"
            p.write_bytes(b"x")
            os.utime(p, (1_700_000_000 + i, 1_700_000_000 + i))
            made.append(p.name)
        dropped = bp.prune(str(self.dest), keep=2)
        left = sorted(os.listdir(self.dest))
        self.assertEqual(len(dropped), 3)
        self.assertEqual(left, made[-2:])

    def test_prune_does_nothing_when_under_the_limit(self):
        (self.dest / "bellows-personal-core-2026-01-01.zip").write_bytes(b"x")
        self.assertEqual(bp.prune(str(self.dest), keep=14), [])
        self.assertEqual(len(os.listdir(self.dest)), 1)

    def test_prune_ignores_files_that_are_not_ours(self):
        (self.dest / "holiday-photos.zip").write_bytes(b"x")
        for i in range(3):
            p = self.dest / f"bellows-personal-core-2026-02-0{i + 1}.zip"
            p.write_bytes(b"x")
            os.utime(p, (1_700_000_000 + i, 1_700_000_000 + i))
        bp.prune(str(self.dest), keep=1)
        self.assertIn("holiday-photos.zip", os.listdir(self.dest))


if __name__ == "__main__":
    unittest.main()


class DestinationIsRealTest(unittest.TestCase):
    """A folder named OneDrive is not OneDrive.

    Windows creates that folder during setup whether or not anyone signs in, so a
    backup written there succeeds, reports success, and uploads nothing. This is the
    one failure the rest of the module cannot catch: every hash matches, the restore
    works, and the archive is still sitting on the disk that was supposed to fail.

    Roots are injected rather than read from the live machine so these assert the
    LOGIC, not whatever happens to be installed on the runner.
    """

    ONEDRIVE_LIVE: ClassVar = [("C:/Users/x/OneDrive", True, "OneDrive account is linked")]
    ONEDRIVE_DEAD: ClassVar = [("C:/Users/x/OneDrive", False, "NO ACCOUNT IS LINKED")]

    def test_a_folder_inside_a_linked_root_is_synced(self):
        state, _ = bp.destination_status("C:/Users/x/OneDrive/Bellows Backups", self.ONEDRIVE_LIVE)
        self.assertEqual(state, "synced")

    def test_the_same_path_with_no_account_linked_is_not(self):
        # Identical path, opposite verdict. The path never told you anything.
        state, why = bp.destination_status(
            "C:/Users/x/OneDrive/Bellows Backups", self.ONEDRIVE_DEAD
        )
        self.assertEqual(state, "unlinked")
        self.assertIn("NO ACCOUNT", why)

    def test_unlinked_is_distinct_from_an_ordinary_local_folder(self):
        # A deliberate second-disk target is a choice; a dead cloud folder is a trap.
        # Collapsing them into one warning would train someone to ignore both.
        local, _ = bp.destination_status("G:/Backups", self.ONEDRIVE_DEAD)
        dead, _ = bp.destination_status("C:/Users/x/OneDrive/Backups", self.ONEDRIVE_DEAD)
        self.assertEqual(local, "local")
        self.assertEqual(dead, "unlinked")
        self.assertNotEqual(local, dead)

    def test_the_root_itself_counts_as_inside_it(self):
        state, _ = bp.destination_status("C:/Users/x/OneDrive", self.ONEDRIVE_LIVE)
        self.assertEqual(state, "synced")

    def test_a_sibling_that_merely_starts_with_the_same_name_is_not_inside(self):
        # "OneDrive-old" must not match "OneDrive" on a bare prefix compare.
        state, _ = bp.destination_status("C:/Users/x/OneDrive-old/Backups", self.ONEDRIVE_LIVE)
        self.assertEqual(state, "local")

    def test_no_cloud_client_at_all_reads_as_local(self):
        state, why = bp.destination_status("C:/anywhere", [])
        self.assertEqual(state, "local")
        self.assertIn("not inside any linked", why)

    def test_detection_never_raises_on_this_machine(self):
        # Registry reads and drive probing must degrade to "found nothing" rather
        # than take the backup down with them, on any platform.
        roots = bp.cloud_roots()
        self.assertIsInstance(roots, list)
        for path, live, why in roots:
            self.assertIsInstance(path, str)
            self.assertIsInstance(live, bool)
            self.assertTrue(why)


class DiscoveryProposesOnlyLiveRootsTest(unittest.TestCase):
    """Auto-discovery must not recommend the trap.

    An unsigned-in OneDrive folder exists on a very large number of Windows
    machines. Discovery that matched on folder name would hand back exactly the
    destination destination_status() refuses, which would be the tool proposing its
    own worst failure mode as the default.
    """

    class _Cfg:
        pass

    def setUp(self):
        self._real = bp.cloud_roots

    def tearDown(self):
        bp.cloud_roots = self._real

    def fake(self, roots):
        bp.cloud_roots = lambda: roots

    def test_a_dead_root_is_never_proposed(self):
        self.fake([("C:/Users/x/OneDrive", False, "NO ACCOUNT IS LINKED")])
        dest, source = bp._dest_from_config(self._Cfg())
        self.assertIsNone(dest)
        self.assertIsNone(source)

    def test_a_live_root_is_proposed(self):
        self.fake([("H:/My Drive", True, "Google Drive mounted at H:")])
        dest, source = bp._dest_from_config(self._Cfg())
        self.assertIn("My Drive", dest)
        self.assertIn("Bellows Backups", dest)
        self.assertIn("Google Drive", source)

    def test_a_live_root_wins_over_a_dead_one_listed_first(self):
        self.fake(
            [
                ("C:/Users/x/OneDrive", False, "NO ACCOUNT IS LINKED"),
                ("H:/My Drive", True, "Google Drive mounted at H:"),
            ]
        )
        dest, _ = bp._dest_from_config(self._Cfg())
        self.assertIn("My Drive", dest)

    def test_an_explicit_setting_always_wins(self):
        # Someone who typed a path meant it, even a local one; the guard warns at
        # write time rather than discovery silently overriding them here.
        self.fake([("H:/My Drive", True, "Google Drive mounted at H:")])
        cfg = self._Cfg()
        cfg.BACKUP_DIR = "G:/Backups"
        dest, source = bp._dest_from_config(cfg)
        self.assertEqual(dest, "G:/Backups")
        self.assertEqual(source, "userconfig.py")


class DriveLetterScanTest(unittest.TestCase):
    """Scan every drive letter, not a plausible-looking subset.

    REGRESSION: the scan started at G on the assumption that a cloud mount lands
    late in the alphabet. A real install mounted at E and the tool reported no
    Google Drive on a machine where Drive was installed, running, and syncing.

    The direction of that failure is what makes it worth a test. It did not write
    anywhere unsafe - the guard refused and exited non-zero, which was correct - but
    it told someone their working cloud backup did not exist, and the obvious next
    move on that advice is to reinstall or repoint something that was already fine.
    Drive takes the first free letter it is offered and the user can override it, so
    there is no subset that is safe to assume.
    """

    def test_every_letter_is_scanned(self):
        missing = [c for c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ" if c not in bp._DRIVE_LETTERS]
        self.assertEqual(missing, [], f"drive letters not scanned: {missing}")

    def test_the_letter_that_actually_broke_it_is_covered(self):
        self.assertIn("E", bp._DRIVE_LETTERS)
