.. _admin-registry-signals:

Signals from AdminRegistry
==========================

The :py:class:`lback.admin.admin_registry.AdminRegistry` class emits the following signals, allowing for extensibility and monitoring of model registration within the administration panel.

.. list-table::
   :widths: 25 50 25
   :header-rows: 1

   * - Signal Name
     - Description
     - Arguments (`kwargs`)
   * - ``admin_registry_initialized``
     - Emitted when the :py:class:`AdminRegistry` instance has been successfully initialized and is ready to register models.
     - ``sender`` (:py:class:`AdminRegistry`): The instance of the registry.
   * - ``admin_model_registered``
     - Emitted when a SQLAlchemy model class is successfully registered with the :py:class:`AdminRegistry`.
     - ``sender`` (:py:class:`AdminRegistry`): The registry instance.<br>``model_class`` (:py:class:`type`): The registered model class.<br>``model_name`` (:py:class:`str`): The original (case-sensitive) name of the model.<br>``lowercase_name`` (:py:class:`str`): The lowercase name used as the internal key for the model.
   * - ``admin_model_registration_failed``
     - Emitted when an attempt to register a model with the :py:class:`AdminRegistry` fails. This signal provides details about the reason for failure.
     - ``sender`` (:py:class:`AdminRegistry`): The registry instance.<br>``model_class`` (:py:class:`type`): The model class that failed to register.<br>``model_name`` (:py:class:`str`): The original name of the model.<br>``error_type`` (:py:class:`str`): A string indicating the reason for failure (``"invalid_class"``, ``"already_registered"``, or ``"exception"``).<br>``exception`` (:py:class:`Exception`, *optional*): The exception object if ``error_type`` is ``"exception"``.