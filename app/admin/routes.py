import json
from urllib.parse import urlparse

from flask import Blueprint, render_template, request, redirect, url_for, flash, Response

from app import db
from app.models import Software, Category

admin_bp = Blueprint("admin", __name__)

_MAX_CATEGORY_NAME = 200


def _is_safe_url(url):
    """Return True if url uses http or https scheme (or is empty)."""
    if not url:
        return True
    try:
        scheme = urlparse(url).scheme.lower()
        return scheme in ("http", "https")
    except Exception:
        return False


def _validate_software_fields(software):
    if not software.name:
        return "Name is required."
    if len(software.name) > 200:
        return "Name must be 200 characters or less."
    if len(software.tagline) > 500:
        return "Tagline must be 500 characters or less."
    return None


@admin_bp.route("/")
def dashboard():
    software = Software.query.order_by(Software.name).all()
    return render_template("admin/dashboard.html", software=software)


@admin_bp.route("/add", methods=["GET", "POST"])
def add():
    categories = Category.query.order_by(Category.category_type, Category.name).all()

    if request.method == "POST":
        software = Software(
            name=request.form.get("name", "").strip(),
            url=request.form.get("url", "").strip(),
            tagline=request.form.get("tagline", "").strip(),
            content=request.form.get("content", "").strip(),
            logo=request.form.get("logo", "").strip(),
            featured="featured" in request.form,
        )

        err = _validate_software_fields(software)
        if err:
            flash(err, "error")
            return render_template("admin/edit.html", software=software, categories=categories, is_new=True)

        if not _is_safe_url(software.url):
            flash("URL must use http:// or https://.", "error")
            return render_template("admin/edit.html", software=software, categories=categories, is_new=True)

        if not _is_safe_url(software.logo):
            flash("Logo URL must use http:// or https://.", "error")
            return render_template("admin/edit.html", software=software, categories=categories, is_new=True)

        selected_ids = request.form.getlist("categories", type=int)
        software.categories = Category.query.filter(Category.id.in_(selected_ids)).all()

        new_cats = request.form.get("new_categories", "").strip()
        if new_cats:
            for cat_name in new_cats.split(","):
                cat_name = cat_name.strip()
                if not cat_name:
                    continue
                if len(cat_name) > _MAX_CATEGORY_NAME:
                    flash(f"Category name must be {_MAX_CATEGORY_NAME} characters or less.", "error")
                    return render_template("admin/edit.html", software=software, categories=categories, is_new=True)
                existing = Category.query.filter_by(name=cat_name).first()
                if existing:
                    if existing not in software.categories:
                        software.categories.append(existing)
                else:
                    cat = Category(name=cat_name, category_type=Category.classify(cat_name))
                    db.session.add(cat)
                    software.categories.append(cat)

        db.session.add(software)
        db.session.commit()
        flash(f'"{software.name}" has been added.', "success")
        return redirect(url_for("admin.dashboard"))

    return render_template("admin/edit.html", software=None, categories=categories, is_new=True)


@admin_bp.route("/edit/<int:software_id>", methods=["GET", "POST"])
def edit(software_id):
    software = db.get_or_404(Software, software_id)
    categories = Category.query.order_by(Category.category_type, Category.name).all()

    if request.method == "POST":
        software.name = request.form.get("name", "").strip()
        software.url = request.form.get("url", "").strip()
        software.tagline = request.form.get("tagline", "").strip()
        software.content = request.form.get("content", "").strip()
        software.logo = request.form.get("logo", "").strip()
        software.featured = "featured" in request.form

        err = _validate_software_fields(software)
        if err:
            flash(err, "error")
            return render_template("admin/edit.html", software=software, categories=categories, is_new=False)

        if not _is_safe_url(software.url):
            flash("URL must use http:// or https://.", "error")
            return render_template("admin/edit.html", software=software, categories=categories, is_new=False)

        if not _is_safe_url(software.logo):
            flash("Logo URL must use http:// or https://.", "error")
            return render_template("admin/edit.html", software=software, categories=categories, is_new=False)

        selected_ids = request.form.getlist("categories", type=int)
        software.categories = Category.query.filter(Category.id.in_(selected_ids)).all()

        new_cats = request.form.get("new_categories", "").strip()
        if new_cats:
            for cat_name in new_cats.split(","):
                cat_name = cat_name.strip()
                if not cat_name:
                    continue
                if len(cat_name) > _MAX_CATEGORY_NAME:
                    flash(f"Category name must be {_MAX_CATEGORY_NAME} characters or less.", "error")
                    return render_template("admin/edit.html", software=software, categories=categories, is_new=False)
                existing = Category.query.filter_by(name=cat_name).first()
                if existing:
                    if existing not in software.categories:
                        software.categories.append(existing)
                else:
                    cat = Category(name=cat_name, category_type=Category.classify(cat_name))
                    db.session.add(cat)
                    software.categories.append(cat)

        db.session.commit()
        flash(f'"{software.name}" has been updated.', "success")
        return redirect(url_for("admin.dashboard"))

    return render_template("admin/edit.html", software=software, categories=categories, is_new=False)


@admin_bp.route("/delete/<int:software_id>", methods=["POST"])
def delete(software_id):
    software = db.get_or_404(Software, software_id)
    name = software.name
    db.session.delete(software)
    db.session.commit()
    flash(f'"{name}" has been deleted.', "success")
    return redirect(url_for("admin.dashboard"))


@admin_bp.route("/export")
def export_backup():
    """Export all software entries as a JSON backup file."""
    from datetime import datetime, timezone

    software_list = Software.query.order_by(Software.name).all()
    data = []
    for s in software_list:
        data.append({
            "name": s.name,
            "url": s.url or "",
            "tagline": s.tagline or "",
            "content": s.content or "",
            "logo": s.logo or "",
            "featured": s.featured,
            "categories": [c.name for c in s.categories],
        })

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    filename = f"software-catalog-backup-{timestamp}.json"
    json_str = json.dumps(data, indent=2, ensure_ascii=False)

    return Response(
        json_str,
        mimetype="application/json",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@admin_bp.route("/import", methods=["POST"])
def import_backup():
    """Import software entries from a JSON backup file."""
    file = request.files.get("backup_file")
    if not file or not file.filename:
        flash("No file selected.", "error")
        return redirect(url_for("admin.dashboard"))

    try:
        data = json.load(file)
    except (json.JSONDecodeError, UnicodeDecodeError):
        flash("Invalid JSON file.", "error")
        return redirect(url_for("admin.dashboard"))

    if not isinstance(data, list):
        flash("Invalid backup format: expected a JSON array.", "error")
        return redirect(url_for("admin.dashboard"))

    mode = request.form.get("import_mode", "merge")

    if mode == "replace":
        db.session.execute(db.text("DELETE FROM software_categories"))
        Software.query.delete()
        Category.query.delete()
        db.session.flush()

    category_cache = {c.name: c for c in Category.query.all()}
    existing_names = {s.name for s in Software.query.all()} if mode == "merge" else set()
    added = 0
    skipped = 0

    for entry in data:
        if not isinstance(entry, dict):
            continue
        name = entry.get("name", "").strip()
        if not name:
            continue

        if mode == "merge" and name in existing_names:
            skipped += 1
            continue

        entry_url = entry.get("url", "").strip()
        entry_logo = entry.get("logo", "").strip()
        if not _is_safe_url(entry_url):
            entry_url = ""
        if not _is_safe_url(entry_logo):
            entry_logo = ""

        software = Software(
            name=name,
            url=entry_url,
            tagline=entry.get("tagline", "").strip(),
            content=entry.get("content", "").strip(),
            logo=entry_logo,
            featured=bool(entry.get("featured", False)),
        )
        db.session.add(software)

        for cat_name in entry.get("categories", []):
            cat_name = cat_name.strip()
            if not cat_name or len(cat_name) > _MAX_CATEGORY_NAME:
                continue
            if cat_name not in category_cache:
                cat = Category(name=cat_name, category_type=Category.classify(cat_name))
                db.session.add(cat)
                db.session.flush()
                category_cache[cat_name] = cat
            software.categories.append(category_cache[cat_name])

        existing_names.add(name)
        added += 1

    db.session.commit()

    if mode == "replace":
        flash(f"Replaced catalog with {added} entries from backup.", "success")
    else:
        msg = f"Imported {added} new entries."
        if skipped:
            msg += f" Skipped {skipped} duplicates."
        flash(msg, "success")

    return redirect(url_for("admin.dashboard"))
